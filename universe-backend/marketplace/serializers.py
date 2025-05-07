# marketplace/serializers.py
from rest_framework import serializers
from .models import MarketplaceItem, ItemImage, MarketplaceMessage

class ItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemImage
        fields = ['id', 'image']

class MarketplaceItemSerializer(serializers.ModelSerializer):
    images = ItemImageSerializer(many=True, read_only=True)
    seller_username = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketplaceItem
        fields = '__all__'
        read_only_fields = ['seller']
    
    def get_seller_username(self, obj):
        return obj.seller.username
    
    def create(self, validated_data):
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)

class MarketplaceMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.SerializerMethodField()
    receiver_username = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketplaceMessage
        fields = '__all__'
        read_only_fields = ['sender']
    
    def get_sender_username(self, obj):
        return obj.sender.username
    
    def get_receiver_username(self, obj):
        return obj.receiver.username
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)