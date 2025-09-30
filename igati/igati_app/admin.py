from django.contrib import admin
from .models import User, Product, Project, Order, OrderItem, Payment

# Register your models here.
admin.site.register(User)
admin.site.register(Product)
admin.site.register(Project)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
