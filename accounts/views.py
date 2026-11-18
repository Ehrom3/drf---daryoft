import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import EmailCode, User
from .serializers import Change, Email, Registration, Reset, Verification


def validated(serializer_class, request):
    serializer = serializer_class(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def send_code(user, purpose):
    records = EmailCode.objects.filter(user=user, purpose=purpose)
    if records.filter(created_at__gt=timezone.now() - timedelta(seconds=60)).exists():
        return
    records.delete()
    code = f'{secrets.randbelow(1000000):06d}'
    EmailCode.objects.create(user=user, purpose=purpose, code=code)
    send_mail('Код Daryoft', f'Ваш код: {code}', None, [user.email])


def consume_code(data, purpose):
    user = User.objects.filter(email=data['email'], is_active=(purpose == 'reset')).first()
    records = EmailCode.objects.filter(user=user, purpose=purpose, code=data['code'],
                                       created_at__gte=timezone.now() - timedelta(minutes=10))
    count, _ = records.delete()
    if not count:
        raise ValidationError({'code': 'Неверный или просроченный код.'})
    return user


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def register(request):
    data = validated(Registration, request)
    user = User.objects.create_user(**data, is_active=False)
    send_code(user, 'register')
    return Response({'detail': 'Проверьте почту.'}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def verify(request):
    user = consume_code(validated(Verification, request), 'register')
    user.is_active = True
    user.save(update_fields=['is_active'])
    return Response(status=204)


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def request_code(request, purpose):
    data = validated(Email, request)
    user = User.objects.filter(email=data['email'], is_active=(purpose == 'reset')).first()
    if user:
        send_code(user, purpose)
    return Response({'detail': 'Если адрес подходит, письмо будет отправлено.'})


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def reset_password(request):
    data = validated(Reset, request)
    user = consume_code(data, 'reset')
    user.set_password(data['password'])
    user.save(update_fields=['password'])
    return Response(status=204)


@api_view(['POST'])
def change_password(request):
    data = validated(Change, request)
    if not request.user.check_password(data['old_password']):
        raise ValidationError({'old_password': 'Неверный пароль.'})
    request.user.set_password(data['new_password'])
    request.user.save(update_fields=['password'])
    return Response(status=204)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    return Response(validated(TokenObtainPairSerializer, request))


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh(request):
    try:
        return Response(validated(TokenRefreshSerializer, request))
    except TokenError:
        raise ValidationError({'refresh': 'Недействительный токен.'})


@api_view(['POST'])
def logout_view(request):
    raw = request.data.get('refresh')
    if not isinstance(raw, str):
        raise ValidationError({'refresh': 'Передайте refresh-токен.'})
    try:
        token = RefreshToken(raw)
        if str(token['user_id']) != str(request.user.pk):
            raise ValidationError({'refresh': 'Токен другого пользователя.'})
        token.blacklist()
    except TokenError:
        raise ValidationError({'refresh': 'Недействительный токен.'})
    return Response(status=204)


@api_view(['GET'])
def profile(request):
    return Response(Registration(request.user).data)
