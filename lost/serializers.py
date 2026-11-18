from rest_framework import serializers
from .models import Item, Response


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'author', 'title', 'description', 'image', 'category', 'city',
                  'location', 'event_date', 'kind', 'status', 'created_at']
        read_only_fields = ['author', 'created_at']


class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = ['id', 'item', 'user', 'message', 'phone', 'created_at']
        read_only_fields = ['item', 'user', 'created_at']


class Filters(serializers.Serializer):
    city = serializers.IntegerField(required=False, min_value=1)
    category = serializers.IntegerField(required=False, min_value=1)
    kind = serializers.ChoiceField(required=False, choices=Item.TYPES)
    q = serializers.CharField(required=False, allow_blank=True)
