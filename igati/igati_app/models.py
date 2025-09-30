from django.db import models

# User model- will store the users of igati
class User(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.date_joined}"

# Product model- will store the products listed by users/igati
class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Ksh{self.price}) {self.stock}"


# Project model- will store the igati projects
class Project(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.owner.email} on {self.created_at}"


# Order model- will store the orders placed by users
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.buyer.email}"


# OrderItem model- will store the items in an order
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot price

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"


# Payment model- will store the payment details for orders
class Payment(models.Model):
    METHOD_CHOICES = [
        ("mpesa", "M-Pesa"),
        ("card", "Card"),
        ("paypal", "PayPal"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.status}"