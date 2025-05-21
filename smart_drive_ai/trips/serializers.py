import pandas as pd
from django.db.models import Avg, Count, Sum
from rest_framework import serializers

from data_processing.classify_trip import classify_trip
from data_processing.dsi_algorithm import get_overall_category
from data_processing.extract_features_single_trip import extract_trip_features
from .models import DrivingStyle, Trip, TripAnalysis, User, UserDrivingProfile


CATEGORIES = {
    'плавный': 'smooth',
    'умеренный': 'moderate',
    'агрессивный': 'aggressive'
}


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


class TripUploadSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки телеметрических данных поездки и
    дальнейшей обработки полученных данных.
    """

    class Meta:
        model = Trip
        fields = ('start_date_time', 'end_date_time', 'sensor_data_file')

    def create(self, validated_data):
        # Вызов родительского метода: создание поездки
        trip = super().create(validated_data)

        # Обработка входного csv файла
        path = trip.sensor_data_file
        stats, user_stats = extract_trip_features(
            df=pd.read_csv(path), filename=path
        )
        # Сохранение результатов обработки в TripAnalysis
        analysis = TripAnalysis.objects.create(trip=trip, **user_stats)

        # Вызов нейронки, получение и сохранение оценки стиля вождения
        category = classify_trip(stats)  # категория на русском
        driving_style = DrivingStyle.objects.create(
            analysis=analysis, category=CATEGORIES.get(category)  # сохранение категории на английском
        )
        # Добавление комментария
        driving_style.add_recommendations()

        # region АГРЕГАЦИЯ

        # Создание агрегированных данных
        aggregated_data = Trip.objects.filter(user=trip.user).select_related(
            'tripanalysis'
        ).aggregate(
            total_trips=Count('id'),
            avg_speed=Avg('tripanalysis__avg_speed'),
            total_distance=Sum('tripanalysis__distance'),
            avg_brakes=Avg('tripanalysis__hard_brakes'),
            avg_accels=Avg('tripanalysis__hard_accels'),
            avg_sharp_turns=Avg('tripanalysis__sharp_turns'),
            avg_gyro_mag=Avg('tripanalysis__avg_gyro_mag'),
        )

        # Сбор данных для определения агрегированной категории
        data = Trip.objects.filter(user=trip.user).values_list(
            'tripanalysis__drivingstyle__timestamp',
            'tripanalysis__drivingstyle__category'
        )
        # Определение агрегированной категории
        overall_category = get_overall_category(list(data))

        # Добавление агрегированной категории
        aggregated_data['overall_category'] = overall_category

        # Сохранение или обновление агрегированных данных,
        # в профиле вождения пользователя
        UserDrivingProfile.objects.update_or_create(
            user=trip.user, defaults=aggregated_data
        )

        # endregion
        return trip


class DrivingStyleSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения оценки стиля вождения."""

    class Meta:
        model = DrivingStyle
        fields = ('category', 'recommendations',)


class TripAnalysisSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения анализа поездки."""

    class Meta:
        model = TripAnalysis
        fields = (
            'avg_speed', 'distance', 'hard_brakes', 'hard_accels',
            'sharp_turns', 'avg_gyro_mag', 'trip_duration',
        )


class TripRetrieveSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения полной информации о поездке."""

    trip_analysis = TripAnalysisSerializer(source='tripanalysis')
    driving_style = DrivingStyleSerializer(source='tripanalysis.drivingstyle')

    class Meta:
        model = Trip
        fields = (
            'id', 'start_date_time', 'end_date_time', 'sensor_data_file',
            'trip_analysis', 'driving_style',
        )


class TripListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения списка поездок."""

    distance = serializers.SerializerMethodField()
    driving_style = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            'id', 'start_date_time', 'end_date_time', 'distance',
            'driving_style',
        )

    def get_distance(self, obj):
        return obj.tripanalysis.distance

    def get_driving_style(self, obj):
        return obj.tripanalysis.drivingstyle.category


class UserDrivingProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения агрегированных показателей."""

    class Meta:
        model = UserDrivingProfile
        exclude = ('id', 'user',)
