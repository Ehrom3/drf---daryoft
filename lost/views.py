from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Category, City, Item
from .serializers import Filters, ItemSerializer, ReplySerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def items(request):
    if request.method == 'POST':
        serializer = ItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=201)
    filters = Filters(data=request.query_params)
    filters.is_valid(raise_exception=True)
    values = dict(filters.validated_data)
    search = values.pop('q', '')
    queryset = Item.objects.filter(**values).order_by('-created_at')
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
    return Response(ItemSerializer(queryset, many=True).data)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'GET':
        return Response(ItemSerializer(item).data)
    if item.author_id != request.user.pk and not request.user.is_staff:
        raise PermissionDenied()
    if request.method == 'DELETE':
        item.delete()
        return Response(status=204)
    serializer = ItemSerializer(item, data=request.data, partial=request.method == 'PATCH')
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['GET', 'POST'])
def replies(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'GET':
        if item.author_id != request.user.pk and not request.user.is_staff:
            raise PermissionDenied()
        return Response(ReplySerializer(item.responses.all(), many=True).data)
    if item.author_id == request.user.pk:
        raise PermissionDenied('Нельзя откликнуться на своё объявление.')
    serializer = ReplySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        serializer.save(item=item, user=request.user)
    except IntegrityError:
        if item.responses.filter(user=request.user).exists():
            return Response({'detail': 'Вы уже откликнулись.'}, status=409)
        raise
    return Response(serializer.data, status=201)


@api_view(['GET'])
def my_items(request):
    return Response(ItemSerializer(request.user.items.order_by('-created_at'), many=True).data)


@api_view(['GET'])
def my_responses(request):
    return Response(ReplySerializer(request.user.response_set.order_by('-created_at'), many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def categories(request):
    return Response(list(Category.objects.order_by('name').values('id', 'name')))


@api_view(['GET'])
@permission_classes([AllowAny])
def cities(request):
    return Response(list(City.objects.order_by('name').values('id', 'name')))
