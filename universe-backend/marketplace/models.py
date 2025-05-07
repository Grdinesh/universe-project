# marketplace/models.py
from django.db import models
from django.contrib.auth.models import User

class MarketplaceItem(models.Model):
    ITEM_TYPES = [
        ('furniture', 'Furniture'),
        ('electronics', 'Electronics'),
        ('books', 'Books'),
        ('clothing', 'Clothing'),
        ('kitchen', 'Kitchen'),
        ('groceries', 'Groceries'),
        ('other', 'Other'),
    ]
    
    CONDITION_TYPES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_items')
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    condition = models.CharField(max_length=20, choices=CONDITION_TYPES, default='good')
    location = models.CharField(max_length=100)
    item_pickup_deadline = models.DateTimeField(null=True, blank=True)
    is_sold = models.BooleanField(default=False)
    posted_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class ItemImage(models.Model):
    item = models.ForeignKey(MarketplaceItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='marketplace_items')
    
    def __str__(self):
        return f"Image for {self.item.title}"

class MarketplaceMessage(models.Model):
    item = models.ForeignKey(MarketplaceItem, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_marketplace_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_marketplace_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} about {self.item.title}"