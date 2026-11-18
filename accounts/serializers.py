from rest_framework import serializers
from .models import User


class Registration(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, trim_whitespace=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password']


class Email(serializers.Serializer):
    email = serializers.EmailField()


class Verification(Email):
    code = serializers.RegexField(r'^[0-9]{6}$')


class Reset(Verification):
    password = serializers.CharField(min_length=8, trim_whitespace=False)


class Change(serializers.Serializer):
    old_password = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(min_length=8, trim_whitespace=False)
