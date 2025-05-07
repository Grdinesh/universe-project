# roommate_matching/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.contrib.auth.models import User
from .models import MatchRequest, CompatibilityScore
from .serializers import MatchRequestSerializer, CompatibilityScoreSerializer, MatchProfileSerializer
from user_profiles.models import UserProfile, RoommateProfile

class MatchRequestViewSet(viewsets.ModelViewSet):
    queryset = MatchRequest.objects.all()
    serializer_class = MatchRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return MatchRequest.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if a request already exists
        receiver_id = serializer.validated_data.get('receiver').id
        existing_request = MatchRequest.objects.filter(
            (Q(sender=request.user) & Q(receiver_id=receiver_id)) |
            (Q(sender_id=receiver_id) & Q(receiver=request.user))
        ).first()
        
        if existing_request:
            return Response(
                {"detail": "A match request already exists between these users."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(sender=request.user, status='pending')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        match_request = self.get_object()
        
        if match_request.receiver != request.user:
            return Response(
                {"detail": "You don't have permission to accept this request."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        match_request.status = 'accepted'
        match_request.save()
        
        return Response({"status": "Match request accepted"})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        match_request = self.get_object()
        
        if match_request.receiver != request.user:
            return Response(
                {"detail": "You don't have permission to reject this request."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        match_request.status = 'rejected'
        match_request.save()
        
        return Response({"status": "Match request rejected"})

class RoommateMatchingViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """
        Get potential roommate matches for the current user
        """
        # Get current user's profile and preferences
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            roommate_profile = RoommateProfile.objects.get(user_profile=user_profile)
        except (UserProfile.DoesNotExist, RoommateProfile.DoesNotExist):
            return Response(
                {"detail": "Please complete your profile to find matches."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all users with roommate profiles, excluding current user
        other_profiles = RoommateProfile.objects.exclude(
            user_profile__user=request.user
        ).select_related('user_profile__user')
        
        # Calculate compatibility scores
        matches = []
        for other_profile in other_profiles:
            other_user = other_profile.user_profile.user
            
            # Get existing compatibility score or calculate a new one
            compatibility, created = CompatibilityScore.objects.get_or_create(
                user1=request.user,
                user2=other_user,
                defaults={'score': self._calculate_compatibility(roommate_profile, other_profile)}
            )
            
            # If the score is old, recalculate it
            if created is False:
                compatibility.score = self._calculate_compatibility(roommate_profile, other_profile)
                compatibility.save()
            
            # Get match status if any
            match_request = MatchRequest.objects.filter(
                (Q(sender=request.user) & Q(receiver=other_user)) |
                (Q(sender=other_user) & Q(receiver=request.user))
            ).first()
            
            match_status = match_request.status if match_request else 'none'
            
            # Add to matches
            matches.append({
                'user': other_user,
                'profile': other_profile.user_profile,
                'roommate_profile': other_profile,
                'compatibility_score': compatibility.score,
                'match_status': match_status
            })
        
        # Sort by compatibility score (highest first)
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        serializer = MatchProfileSerializer(matches, many=True)
        return Response(serializer.data)
    
    def _calculate_compatibility(self, user_profile, other_profile):
        """
        Calculate compatibility score between two roommate profiles
        Returns a score between 0-100
        """
        score = 0
        total_weight = 0
        
        # Smoking preference (weight: 15)
        if user_profile.smoking_preference != 'no_preference' and other_profile.smoking_preference != 'no_preference':
            weight = 15
            total_weight += weight
            if user_profile.smoking_preference == other_profile.smoking_preference:
                score += weight
        
        # Drinking preference (weight: 10)
        if user_profile.drinking_preference != 'no_preference' and other_profile.drinking_preference != 'no_preference':
            weight = 10
            total_weight += weight
            if user_profile.drinking_preference == other_profile.drinking_preference:
                score += weight
        
        # Sleep habits (weight: 20)
        if user_profile.sleep_habits != 'no_preference' and other_profile.sleep_habits != 'no_preference':
            weight = 20
            total_weight += weight
            if user_profile.sleep_habits == other_profile.sleep_habits:
                score += weight
        
        # Study habits (weight: 15)
        if user_profile.study_habits != 'no_preference' and other_profile.study_habits != 'no_preference':
            weight = 15
            total_weight += weight
            if user_profile.study_habits == other_profile.study_habits:
                score += weight
        
        # Guests preference (weight: 10)
        if user_profile.guests_preference != 'no_preference' and other_profile.guests_preference != 'no_preference':
            weight = 10
            total_weight += weight
            if user_profile.guests_preference == other_profile.guests_preference:
                score += weight
        
        # Cleanliness level (weight: 20)
        weight = 20
        total_weight += weight
        cleanliness_diff = abs(user_profile.cleanliness_level - other_profile.cleanliness_level)
        if cleanliness_diff == 0:
            score += weight
        elif cleanliness_diff == 1:
            score += weight * 0.7
        elif cleanliness_diff == 2:
            score += weight * 0.4
        
        # Budget compatibility (weight: 10)
        if user_profile.max_rent_budget and other_profile.max_rent_budget:
            weight = 10
            total_weight += weight
            budget_diff_percentage = abs(user_profile.max_rent_budget - other_profile.max_rent_budget) / max(user_profile.max_rent_budget, other_profile.max_rent_budget)
            if budget_diff_percentage <= 0.1:
                score += weight
            elif budget_diff_percentage <= 0.2:
                score += weight * 0.7
            elif budget_diff_percentage <= 0.3:
                score += weight * 0.4
        
        # Calculate final percentage score
        final_score = (score / total_weight * 100) if total_weight > 0 else 50
        return round(final_score, 1)