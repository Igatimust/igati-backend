import requests
import json
from datetime import datetime
import secrets

class PaystackPayment:
    def __init__(self, secret_key=None):
        # IGATI test key
        self.secret_key = secret_key or "sk_test_ba50b587ee77071b2f637fdf381578fce9d3358b"
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    def initialize_payment(self, email, amount, currency="KES", callback_url=None, phone=None):
        """Initialize payment with Paystack"""
        url = f"{self.base_url}/transaction/initialize"
        
        # Convert amount to kobo/cents (Paystack uses smallest currency unit)
        amount_in_kobo = int(amount * 100)
        
        data = {
            "email": email,
            "amount": amount_in_kobo,
            "currency": currency,
            "reference": self.generate_reference(),
            "callback_url": callback_url or "http://localhost:5000/payment/callback",
            "metadata": {
                "business_name": "IGATI",
                "business_description": "Empowering changemakers through a collaborative ecosystem",
                "industry": "Agriculture - Agricultural cooperatives"
            }
        }
        
        # Add phone number if provided
        if phone and phone.strip():
            data["metadata"]["phone_number"] = phone.strip()
            # For mobile money, set channels
            data["channels"] = ["mobile_money", "card", "bank_transfer", "ussd"]
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            result = response.json()
            
            if result.get("status"):
                return {
                    "success": True,
                    "authorization_url": result["data"]["authorization_url"],
                    "access_code": result["data"]["access_code"],
                    "reference": result["data"]["reference"],
                    "amount": amount,
                    "currency": currency
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Payment initialization failed")
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Network error: {str(e)}"
            }
    
    def verify_payment(self, reference):
        """Verify payment status"""
        url = f"{self.base_url}/transaction/verify/{reference}"
        
        try:
            response = requests.get(url, headers=self.headers)
            result = response.json()
            
            if result.get("status"):
                data = result["data"]
                return {
                    "success": True,
                    "status": data["status"],
                    "amount": data["amount"] / 100,  # Convert back from kobo
                    "currency": data["currency"],
                    "reference": data["reference"],
                    "channel": data.get("channel", "unknown"),
                    "paid_at": data.get("paid_at"),
                    "customer_email": data["customer"]["email"]
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Verification failed")
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Verification error: {str(e)}"
            }
    
    def generate_reference(self):
        """Generate unique payment reference"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4).upper()
        return f"IGATI_{timestamp}_{random_part}"
    
    def get_supported_channels(self):
        """Get available payment channels"""
        return [
            {"name": "M-Pesa", "code": "mobile_money", "description": "Pay with M-Pesa"},
            {"name": "Airtel Money", "code": "mobile_money", "description": "Pay with Airtel Money"},
            {"name": "Credit Card", "code": "card", "description": "Pay with Visa/Mastercard"},
            {"name": "Bank Transfer", "code": "bank_transfer", "description": "Pay via bank transfer"},
            {"name": "USSD", "code": "ussd", "description": "Pay with USSD code"}
        ]

# Simulation class for testing without real Paystack account
class PaystackSimulator:
    def __init__(self):
        self.transactions = {}
        self.business_name = "IGATI"
        self.business_description = "Empowering changemakers through a collaborative ecosystem"
        # IGATI real test keys
        self.test_secret_key = "sk_test_ba50b587ee77071b2f637fdf381578fce9d3358b"
        self.test_public_key = "pk_test_50e5b127373ada2a4c90e48d413f94df5c993b1d"
    
    def initialize_payment(self, email, amount, currency="KES", callback_url=None, phone=None):
        """Simulate Paystack payment initialization"""
        reference = self.generate_reference()
        
        # Store transaction for simulation
        self.transactions[reference] = {
            "email": email,
            "amount": amount,
            "currency": currency,
            "phone": phone,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "authorization_url": f"https://checkout.paystack.com/simulate/{reference}",
            "access_code": f"access_{reference}",
            "reference": reference,
            "amount": amount,
            "currency": currency,
            "business_name": self.business_name,
            "message": f"Payment initialized for {self.business_name} (SIMULATION)"
        }
    
    def verify_payment(self, reference):
        """Simulate payment verification"""
        if reference not in self.transactions:
            return {
                "success": False,
                "message": "Transaction not found"
            }
        
        transaction = self.transactions[reference]
        
        # Simulate successful payment
        transaction["status"] = "success"
        transaction["paid_at"] = datetime.now().isoformat()
        transaction["channel"] = "mobile_money"  # Simulate M-Pesa
        
        return {
            "success": True,
            "status": "success",
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "reference": reference,
            "channel": "mobile_money",
            "paid_at": transaction["paid_at"],
            "customer_email": transaction["email"]
        }
    
    def generate_reference(self):
        """Generate unique payment reference for IGATI"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4).upper()
        return f"IGATI_SIM_{timestamp}_{random_part}"
    
    def get_supported_channels(self):
        """Get available payment channels"""
        return [
            {"name": "M-Pesa", "code": "mobile_money", "description": "Pay with M-Pesa (Simulated)"},
            {"name": "Airtel Money", "code": "mobile_money", "description": "Pay with Airtel Money (Simulated)"},
            {"name": "Credit Card", "code": "card", "description": "Pay with Visa/Mastercard (Simulated)"}
        ]

# Test the integration
if __name__ == "__main__":
    print("=== PAYSTACK INTEGRATION TEST ===\n")
    
    # Use simulator for testing
    paystack = PaystackSimulator()
    
    # Test 1: Initialize payment
    print("1. Initializing Payment:")
    init_result = paystack.initialize_payment(
        email="test@example.com",
        amount=1500.00,
        currency="KES"
    )
    print(f"   Result: {init_result}")
    
    if init_result["success"]:
        reference = init_result["reference"]
        
        # Test 2: Verify payment
        print(f"\n2. Verifying Payment (Reference: {reference}):")
        verify_result = paystack.verify_payment(reference)
        print(f"   Result: {verify_result}")
        
        # Test 3: Show supported channels
        print(f"\n3. Supported Payment Channels:")
        channels = paystack.get_supported_channels()
        for channel in channels:
            print(f"   - {channel['name']}: {channel['description']}")
    
    print(f"\n PAYSTACK TEST COMPLETE")