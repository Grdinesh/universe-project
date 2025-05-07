# user_profiles/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, RoommateProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user']

    def update(self, instance, validated_data):
        # Update user's first_name and last_name if provided
        if 'first_name' in validated_data:
            instance.user.first_name = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            instance.user.last_name = validated_data.pop('last_name')
        instance.user.save()
        
        # Update the profile fields
        return super().update(instance, validated_data)

class RoommateProfileSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = RoommateProfile
        fields = '__all__'
        read_only_fields = ['user_profile']