import pandas as pd
from rest_framework import serializers

from .extract_features_single_trip import extract_trip_features
from .models import Trip, TripAnalysis, User


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


class TripSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки телеметрических данных поездки,
    дальнейшей обработки полученных данных
    и сохранения результатов обработки в таблицу TripAnalysis.
    """

    class Meta:
        model = Trip
        fields = ('start_time', 'end_time', 'sensor_data_file')

    def create(self, validated_data):
        trip = super().create(validated_data)

        # region Обработка входного csv файла
        path = trip.sensor_data_file
        stats, user_stats = extract_trip_features(
            df=pd.read_csv(path), filename=path
        )
        # endregion
        # region Сохранение результатов обработки в TripAnalysis
        TripAnalysis.objects.create(
            trip=trip,
            avg_speed=user_stats['avg_speed'],
            distance=user_stats['distance'],
            hard_brakes=user_stats['hard_brakes'],
            hard_accels=user_stats['hard_accels'],
            avg_gyro_mag=user_stats['avg_gyro_mag'],
            sharp_turns=user_stats['sharp_turns'],
            trip_duration=user_stats['trip_duration']
        )
        # endregion
        return trip
