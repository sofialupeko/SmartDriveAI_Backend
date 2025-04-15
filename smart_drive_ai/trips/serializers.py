from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрация нового пользователя."""

    class Meta:
        model = User
        fields = ('name', 'email', 'phone', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        """Сохранение хешированного пароля."""
        user = super().create(validated_data)
        user.set_password(user.password)
        user.save()
        return user
