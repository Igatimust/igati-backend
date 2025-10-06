from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string

class PaymentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('expired', 'Expired'),
        ('failed', 'Failed'),
    ]
    
    reference_no = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user_id = models.CharField(max_length=50, default='guest')
    email = models.EmailField(max_length=255, default='customer@email.com')
    phone = models.CharField(max_length=20, blank=True, null=True, default='')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_channel = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    authorization_url = models.URLField(max_length=500, blank=True, null=True)
    access_code = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, default='KES')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = self.generate_unique_reference()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def generate_unique_reference(self):
        while True:
            reference = ''.join(random.choices(string.digits, k=10))
            if not PaymentRequest.objects.filter(reference_no=reference).exists():
                return reference
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Payment {self.reference_no} - KES {self.amount}"