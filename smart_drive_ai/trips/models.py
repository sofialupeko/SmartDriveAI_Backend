from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractBaseUser):
    """Пользователь."""
    name = models.CharField('Имя', max_length=100, blank=True, null=True)
    email = models.EmailField(
        'Email', max_length=100, unique=True, blank=False, null=False
    )
    phone = PhoneNumberField('Телефон', region='RU', blank=True, null=True)
    registration_date = models.DateTimeField(
        'Дата и время регистрации', default=timezone.now
    )
    USERNAME_FIELD = 'email'
    objects = UserManager()


class Trip(models.Model):
    """Поездка."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    start_time = models.DateTimeField('Дата и время начала')
    end_time = models.DateTimeField('Дата и время окончания')
    sensor_data_file = models.FileField('Файл с данными с датчиков')


class TripAnalysis(models.Model):
    """Анализ поездки."""
    trip = models.OneToOneField(
        Trip, on_delete=models.CASCADE, verbose_name='Поездка'
    )
    avg_speed = models.FloatField('Средняя скорость (км/ч)')
    distance = models.FloatField('Пройденное расстояние (км)')
    hard_brakes = models.IntegerField('Частота резких торможений')
    hard_accels = models.IntegerField('Частота резких ускорений')
    avg_yaw_rate = models.FloatField('Средняя угловая скорость')
    sharp_turns = models.IntegerField('Число резких маневров')


class DrivingStyle(models.Model):
    """Оценка стиля вождения."""
    analysis = models.OneToOneField(
        TripAnalysis, on_delete=models.CASCADE, verbose_name='Анализ поездки'
    )
    category = models.CharField('Категория стиля', max_length=50)
    recommendations = models.TextField('Рекомендации')


class UserDrivingProfile(models.Model):
    """Профиль вождения пользователя."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    total_trips = models.IntegerField('Общее число поездок')
    total_distance = models.FloatField('Пройденное расстояние (км)')
    avg_speed = models.FloatField('Средняя скорость (км/ч)')
    avg_brakes = models.FloatField('Среднее число резких торможений')
    avg_accels = models.FloatField('Среднее число резких ускорений')
    avg_yaw_rate = models.FloatField('Средняя угловая скорость')
    overall_category = models.CharField('Общая категория стиля', max_length=50)
