# user_profiles/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import UserProfile, RoommateProfile
from .serializers import UserSerializer, UserProfileSerializer, RoommateProfileSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.query_params.get('current_user', None):
            return UserProfile.objects.filter(user=self.request.user)
        return super().get_queryset()
    
    def create(self, request, *args, **kwargs):
        """
        Create a profile for the current user, or for a specified user if admin.
        """
        # Check if user already has a profile
        user_id = request.data.get('user', request.user.id)
        
        # Non-admins can only create profiles for themselves
        if not request.user.is_staff and int(user_id) != request.user.id:
            return Response(
                {"detail": "You do not have permission to create profiles for other users."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if profile already exists
        if UserProfile.objects.filter(user_id=user_id).exists():
            return Response(
                {"detail": "User already has a profile. Use PATCH to update it."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set user ID in data and proceed with creation
        mutable_data = request.data.copy()
        mutable_data['user'] = user_id
        
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Make sure the profile is created with the correct user."""
        user_id = serializer.validated_data.get('user', self.request.user.id)
        user = User.objects.get(id=user_id)
        serializer.save(user=user)
    
    def update(self, request, *args, **kwargs):
        """
        Update a profile, ensuring users can only update their own profiles.
        """
        instance = self.get_object()
        
        # Non-admins can only update their own profiles
        if not request.user.is_staff and instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to update this profile."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get', 'post'])
    def me(self, request):
        """
        Get or create the current user's profile.
        """
        if request.method == 'GET':
            # Get current user's profile
            try:
                profile = UserProfile.objects.get(user=request.user)
                serializer = self.get_serializer(profile)
                return Response(serializer.data)
            except UserProfile.DoesNotExist:
                return Response(
                    {"detail": "Profile not found. Create it with a POST request."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif request.method == 'POST':
            # Check if user already has a profile
            if UserProfile.objects.filter(user=request.user).exists():
                return Response(
                    {"detail": "You already have a profile. Use PATCH to update it."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create profile for current user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        """
        Update the current user's profile.
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "Profile not found. Create it with a POST request to /api/profiles/me/."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

class RoommateProfileViewSet(viewsets.ModelViewSet):
    queryset = RoommateProfile.objects.all()
    serializer_class = RoommateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Optionally filter by user profile.
        """
        queryset = super().get_queryset()
        user_profile_id = self.request.query_params.get('user_profile', None)
        if user_profile_id:
            queryset = queryset.filter(user_profile_id=user_profile_id)
        
        # Filter to show only the current user's roommate profile
        current_user = self.request.query_params.get('current_user', None)
        if current_user and current_user.lower() == 'true':
            queryset = queryset.filter(user_profile__user=self.request.user)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new roommate profile, ensuring user_profile is properly set.
        """
        # Check if user_profile is in the request data
        user_profile_id = request.data.get('user_profile')
        
        if not user_profile_id:
            return Response(
                {"error": "user_profile is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the user_profile exists and belongs to the requesting user
        try:
            user_profile = UserProfile.objects.get(id=user_profile_id)
            # Check if the user is allowed to create this profile
            if user_profile.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You do not have permission to create a profile for this user"},
                    status=status.HTTP_403_FORBIDDEN
                )
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "The specified user_profile does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if a roommate profile already exists for this user_profile
        if RoommateProfile.objects.filter(user_profile_id=user_profile_id).exists():
            return Response(
                {"error": "A roommate profile already exists for this user"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the roommate profile
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user_profile=user_profile)  # Explicitly set the user_profile
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    def perform_create(self, serializer):
        """
        This method is overridden to avoid the default implementation,
        as we're handling the user_profile assignment in create().
        """
        pass  # Do nothing here, we're handling this in create()
    
    @action(detail=False, methods=['get', 'post', 'patch'])
    def me(self, request):
        """
        Get, create, or update the current user's roommate profile.
        """
        if request.method == 'GET':
            # Get current user's roommate profile
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                roommate_profile = RoommateProfile.objects.get(user_profile=user_profile)
                serializer = self.get_serializer(roommate_profile)
                return Response(serializer.data)
            except (UserProfile.DoesNotExist, RoommateProfile.DoesNotExist):
                return Response(
                    {"detail": "Roommate profile not found. Create it with a POST request."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif request.method == 'POST':
            # Get the user's profile
            try:
                user_profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                return Response(
                    {"detail": "You need to create a user profile first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if roommate profile already exists
            if RoommateProfile.objects.filter(user_profile=user_profile).exists():
                return Response(
                    {"detail": "You already have a roommate profile. Use PATCH to update it."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create roommate profile
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user_profile=user_profile)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'PATCH':
            # Get the user's roommate profile
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                roommate_profile = RoommateProfile.objects.get(user_profile=user_profile)
            except UserProfile.DoesNotExist:
                return Response(
                    {"detail": "You need to create a user profile first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except RoommateProfile.DoesNotExist:
                return Response(
                    {"detail": "Roommate profile not found. Create it with a POST request."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update roommate profile
            serializer = self.get_serializer(roommate_profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data)