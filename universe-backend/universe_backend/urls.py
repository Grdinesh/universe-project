"""
URL configuration for universe_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# universe_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.conf.urls.static import static
# from auth_api.views import AuthViewSet, CustomAuthToken

# User serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

# Register view
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=serializer.context).data,
            "message": "User created successfully",
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# User detail view
@api_view(['GET'])
def user_detail(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

# Create a router and register our viewsets with it
router = routers.DefaultRouter()
# router.register(r'auth', AuthViewSet, basename='auth')
from user_profiles.views import UserViewSet, UserProfileViewSet, RoommateProfileViewSet
from marketplace.views import MarketplaceItemViewSet, MarketplaceMessageViewSet
from roommate_matching.views import MatchRequestViewSet, RoommateMatchingViewSet

# router = DefaultRouter()
# router.register(r'auth', AuthViewSet, basename='auth')
# # User Profiles
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'roommate-profiles', RoommateProfileViewSet)
# Marketplace
router.register(r'marketplace-items', MarketplaceItemViewSet)
router.register(r'marketplace-messages', MarketplaceMessageViewSet)
# Roommate Matching
router.register(r'match-requests', MatchRequestViewSet)
router.register(r'roommate-matches', RoommateMatchingViewSet, basename='roommate-matches')

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('api/', include('api.urls')),  # Your existing API URLs
#     path('api/auth/', include('auth_api.urls')),  # New auth URLs
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = [
    path('admin/', admin.site.urls),
    # JWT authentication
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/register/', register, name='register'),
    # path('api/user/', user_detail, name='user_detail'),
    path('api/', include(router.urls)),
    path('api/auth/', include('auth_api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    # path('api/token-auth/', CustomAuthToken.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)