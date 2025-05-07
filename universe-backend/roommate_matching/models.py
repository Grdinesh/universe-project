# roommate_matching/models.py
from django.db import models
from django.contrib.auth.models import User
from user_profiles.models import UserProfile, RoommateProfile

class MatchRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_roommate_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_roommate_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['sender', 'receiver']
    
    def __str__(self):
        return f"Request from {self.sender.username} to {self.receiver.username} - {self.status}"

class CompatibilityScore(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compatibility_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compatibility_as_user2')
    score = models.FloatField()  # 0-100 score
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
    
    def __str__(self):
        return f"Compatibility between {self.user1.username} and {self.user2.username}: {self.score}%"