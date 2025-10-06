"""
Simple Payment System with Database Integration
Uses Flask for easy testing + Django database for storage
"""

from flask import Flask, render_template, request, jsonify
from paystack_integration import PaystackPayment
import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_project.settings')
django.setup()

# import Django models
from payments.models import PaymentRequest
from django.utils import timezone

app = Flask(__name__)
paystack = PaystackPayment()

@app.route('/')
def home():
    return render_template('simple.html')

@app.route('/pay', methods=['POST'])
def process_payment():
    try:
        data = request.json
        email = data.get('email')
        amount = float(data.get('amount'))
        method = data.get('method')
        user_id = data.get('user_id', 'guest')
        phone = data.get('phone', '')
        
        if method == 'paystack':
            # Use Paystack for all payments
            callback_url = "http://localhost:5000/payment/callback"
            
            # Initialize payment with Paystack
            result = paystack.initialize_payment(
                email=email, 
                amount=amount, 
                callback_url=callback_url,
                phone=phone
            )
            
            if result['success']:
                # Save to Django database
                payment = PaymentRequest.objects.create(
                    reference_no=result['reference'],
                    amount=amount,
                    user_id=user_id,
                    email=email,
                    phone=phone,
                    currency='KES',
                    authorization_url=result['authorization_url'],
                    access_code=result.get('access_code', ''),
                    status='pending',
                    metadata={
                        'initialized_at': timezone.now().isoformat(),
                        'callback_url': callback_url,
                        'method': method
                    }
                )
                
                print(f"Payment saved to database: {payment.reference_no}")
                
                return jsonify({
                    'success': True,
                    'payment_url': result['authorization_url'],
                    'reference': result['reference'],
                    'message': f'Payment of KES {amount} initialized successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result['message']
                })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid payment method'
            })
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/payment/callback')
def payment_callback():
    """Handle successful payment callback from Paystack"""
    reference = request.args.get('reference') or request.args.get('trxref')
    
    if reference:
        # Verify the payment with Paystack
        result = paystack.verify_payment(reference)
        
        if result.get('success') and result.get('status') == 'success':
            try:
                # Update database
                payment = PaymentRequest.objects.get(reference_no=reference)
                payment.status = 'paid'
                payment.payment_method = 'paystack'
                payment.payment_channel = result.get('channel', 'unknown')
                payment.paid_at = timezone.now()
                payment.transaction_id = reference
                
                # Update metadata
                if payment.metadata:
                    payment.metadata['verified_at'] = timezone.now().isoformat()
                    payment.metadata['verification_data'] = result
                else:
                    payment.metadata = {
                        'verified_at': timezone.now().isoformat(),
                        'verification_data': result
                    }
                
                payment.save()
                
                print(f"Payment updated in database: {reference} - Status: PAID")
                
                return render_template('success.html', 
                                     reference=reference,
                                     amount=result.get('amount'),
                                     channel=result.get('channel'),
                                     email=result.get('customer_email'))
            except PaymentRequest.DoesNotExist:
                print(f"Payment not found in database: {reference}")
                return render_template('success.html', 
                                     reference=reference,
                                     amount=result.get('amount'),
                                     channel=result.get('channel'),
                                     email=result.get('customer_email'))
        else:
            # Update to failed
            try:
                payment = PaymentRequest.objects.get(reference_no=reference)
                payment.status = 'failed'
                payment.save()
                print(f"Payment failed: {reference}")
            except:
                pass
            
            return render_template('failed.html', 
                                 reference=reference,
                                 message=result.get('message', 'Payment verification failed'))
    else:
        return render_template('failed.html', 
                             message='No payment reference provided')

@app.route('/verify', methods=['POST'])
def verify_payment():
    try:
        data = request.json
        reference = data.get('reference')
        
        result = paystack.verify_payment(reference)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Verification error: {str(e)}'
        })

@app.route('/payments/list')
def list_payments():
    """View all payments from database"""
    try:
        payments = PaymentRequest.objects.all().order_by('-created_at')[:20]
        
        payments_list = []
        for p in payments:
            payments_list.append({
                'reference': p.reference_no,
                'amount': float(p.amount),
                'email': p.email,
                'status': p.status,
                'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'paid_at': p.paid_at.strftime('%Y-%m-%d %H:%M:%S') if p.paid_at else None
            })
        
        return jsonify({
            'success': True,
            'count': len(payments_list),
            'payments': payments_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

if __name__ == '__main__':
    print("=" * 60)
    print("SIMPLE IGATI PAYMENT SYSTEM WITH DATABASE")
    print("=" * 60)
    print("Connected to Django database")
    print("Payments will be saved automatically")
    print("")
    print("Server: http://localhost:5000")
    print("View payments: http://localhost:5000/payments/list")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(debug=True, port=5000)
