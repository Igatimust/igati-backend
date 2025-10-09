from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PaymentRequest
import json
import requests

# Paystack Secret Key
PAYSTACK_SECRET_KEY = "sk_test_ba50b587ee77071b2f637fdf381578fce9d3358b"

@api_view(["POST"])
def initialize_payment(request):
    """
    Initialize Paystack Payment
    
    Request Body:
    {
        "amount": 1500.00,
        "email": "customer@email.com",
        "transaction_reference": "TXN_12345" (optional),
        "metadata": {} (optional),
        "user_id": "user123" (optional),
        "phone_number": "+254712345678" (optional)
    }
    """
    amount = request.data.get("amount")
    email = request.data.get("email", "customer@email.com")
    transaction_reference = request.data.get("transaction_reference")
    metadata = request.data.get("metadata", {})
    user_id = request.data.get("user_id", "guest")
    phone_number = request.data.get("phone_number", "N/A")
    
    print(f"Initializing payment - User: {user_id}, Amount: {amount}, Reference: {transaction_reference}")
    
    # Validate amount
    if not amount:
        return Response({"error": "Amount is required"}, status=400)
    
    try:
        amount_float = float(amount)
        amount_in_kobo = int(amount_float * 100)  # Convert to kobo
    except Exception:
        return Response({"error": "Invalid amount"}, status=400)
    
    # Check for existing pending payment for this user
    existing_payment = PaymentRequest.objects.filter(
        user_id=user_id,
        status="pending"
    ).first()
    
    if existing_payment:
        return JsonResponse({
            "error": "You already have a pending payment.",
            "reference": existing_payment.reference_no,
            "status": existing_payment.status
        }, status=210)
    
    # Build callback URL
    callback_url = request.build_absolute_uri('/payments/callback/')
    
    # Prepare Paystack payload
    payload = {
        "email": email,
        "amount": amount_in_kobo,
        "callback_url": callback_url,
        "metadata": {
            "user_id": user_id,
            "phone_number": phone_number,
            **metadata
        }
    }
    
    # Add custom reference if provided
    if transaction_reference:
        payload["reference"] = transaction_reference
    
    # Call Paystack API
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    res = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=payload,
        headers=headers
    )
    
    paystack_response = res.json()
    
    # Check if initialization was successful
    if paystack_response.get("status"):
        data = paystack_response.get("data", {})
        reference = data.get("reference")
        authorization_url = data.get("authorization_url")
        access_code = data.get("access_code")
        
        # Save payment to database
        payment = PaymentRequest.objects.create(
            reference_no=reference,
            amount=amount_float,
            user_id=user_id,
            email=email,
            phone=phone_number,
            currency="KES",
            authorization_url=authorization_url,
            access_code=access_code,
            status="pending",
            metadata={
                "initialized_at": timezone.now().isoformat(),
                "callback_url": callback_url,
                **metadata
            }
        )
        
        print(f"Payment initialized successfully: {reference}")
    
    return Response(paystack_response)

@api_view(['GET'])
def payment_callback(request):
    """
    Payment Callback - Verify and Save Payment
    
    GET Parameters:
    - reference: Payment reference number
    """
    reference = request.GET.get('reference')
    
    if not reference:
        return render(request, 'failed.html', {
            'message': 'No payment reference provided'
        })
    
    # Verify payment with Paystack
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    
    response = requests.get(url, headers=headers).json()
    
    print("PAYSTACK VERIFY RESPONSE:", response)
    
    # Ensure "data" exists and is a dict
    data = response.get("data", None)
    if not data or not isinstance(data, dict):
        return JsonResponse({
            "error": "Invalid Paystack response",
            "details": response
        }, status=400)
    
    if data.get("status") == "success":
        try:
            # Extract metadata
            metadata = data.get("metadata") or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            user_id = metadata.get("user_id", "guest")
            phone_number = metadata.get("phone_number", "N/A")
            total_amount = data.get("amount", 0) / 100  # Convert from kobo
            method = "paystack"
            transaction_reference = reference
            
            # Get payment record
            try:
                payment = PaymentRequest.objects.get(reference_no=reference)
                
                # Update payment status
                payment.status = "paid"
                payment.payment_method = method
                payment.payment_channel = data.get("channel", "unknown")
                payment.paid_at = timezone.now()
                payment.transaction_id = transaction_reference
                
                # Update metadata
                if payment.metadata:
                    payment.metadata['verified_at'] = timezone.now().isoformat()
                    payment.metadata['verification_data'] = data
                else:
                    payment.metadata = {
                        'verified_at': timezone.now().isoformat(),
                        'verification_data': data
                    }
                
                payment.save()
                
                print(f"Payment {reference} marked as paid")
                
                # Render success page
                return render(request, "success.html", {
                    "reference": payment.reference_no,
                    "amount": float(payment.amount),
                    "currency": payment.currency,
                    "email": payment.email,
                    "paid_at": payment.paid_at
                })
                
            except PaymentRequest.DoesNotExist:
                return JsonResponse({"error": "Payment record not found"}, status=404)
            
        except Exception as e:
            print(f"Error processing payment: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    
    return render(request, 'failed.html', {
        'message': 'Payment verification failed',
        'reference': reference
    })

@api_view(["GET"])
def check_payment_status(request, reference_no):
    """
    API 3: Check Payment Status
    
    GET /payments/status/<reference_no>/
    
    Response:
    {
        "success": true,
        "reference_no": "IGATI_20250105_ABC123",
        "amount": 1500.00,
        "currency": "KES",
        "status": "paid",
        "email": "user@example.com",
        "payment_channel": "mobile_money",
        "created_at": "2025-01-05 12:00:00",
        "paid_at": "2025-01-05 12:05:00"
    }
    """
    try:
        payment = PaymentRequest.objects.get(reference_no=reference_no)
        
        return JsonResponse({
            'success': True,
            'reference_no': payment.reference_no,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'status': payment.status,
            'email': payment.email,
            'phone': payment.phone,
            'user_id': payment.user_id,
            'payment_method': payment.payment_method,
            'payment_channel': payment.payment_channel,
            'description': payment.description,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'expires_at': payment.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'paid_at': payment.paid_at.strftime('%Y-%m-%d %H:%M:%S') if payment.paid_at else None,
            'is_expired': payment.is_expired()
        })
    except PaymentRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment not found'
        }, status=404)


@api_view(["GET"])
def list_payments(request):
    """
    API 4: List All Payments (Optional - for admin/debugging)
    
    GET /payments/list/?user_id=user123&status=paid
    """
    user_id = request.GET.get('user_id')
    status = request.GET.get('status')
    
    payments = PaymentRequest.objects.all().order_by('-created_at')
    
    if user_id:
        payments = payments.filter(user_id=user_id)
    if status:
        payments = payments.filter(status=status)
    
    payments_data = []
    for payment in payments[:50]:  # Limit to 50 records
        payments_data.append({
            'reference_no': payment.reference_no,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'status': payment.status,
            'email': payment.email,
            'user_id': payment.user_id,
            'payment_channel': payment.payment_channel,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'paid_at': payment.paid_at.strftime('%Y-%m-%d %H:%M:%S') if payment.paid_at else None
        })
    
    return JsonResponse({
        'success': True,
        'count': len(payments_data),
        'payments': payments_data
    })