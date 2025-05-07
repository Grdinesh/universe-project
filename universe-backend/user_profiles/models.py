# user_profiles/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    interests = models.TextField(blank=True)
    course_major = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics', null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class RoommateProfile(models.Model):
    PREFERENCE_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('sometimes', 'Sometimes'),
        ('no_preference', 'No Preference'),
    ]
    
    SLEEP_HABITS = [
        ('early_riser', 'Early Riser'),
        ('night_owl', 'Night Owl'),
        ('average', 'Average'),
    ]
    
    STUDY_HABITS = [
        ('in_room', 'In Room'),
        ('library', 'Library'),
        ('other_places', 'Other Places'),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='roommate_profile')
    smoking_preference = models.CharField(max_length=20, choices=PREFERENCE_CHOICES, default='no_preference')
    drinking_preference = models.CharField(max_length=20, choices=PREFERENCE_CHOICES, default='no_preference')
    sleep_habits = models.CharField(max_length=20, choices=SLEEP_HABITS, default='average')
    study_habits = models.CharField(max_length=20, choices=STUDY_HABITS, default='library')
    guests_preference = models.CharField(max_length=20, choices=PREFERENCE_CHOICES, default='no_preference')
    cleanliness_level = models.IntegerField(default=3, help_text="Scale of 1-5, 5 being the cleanest")
    max_rent_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_move_in_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user_profile.user.username}'s roommate preferences"