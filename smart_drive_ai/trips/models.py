from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


CATEGORIES = (
    ('smooth', 'плавный'),
    ('moderate', 'умеренный'),
    ('aggressive', 'агрессивный'),
)

RECOMMENDATIONS = {
    'smooth': (
        '• Поддерживайте плавность хода — без резких разгонов и торможений.\n'
        '• Держите ровную скорость, при возможности включайт)е круиз‑контроль.\n'
        '• Проверяйте давление в шинах хотя бы раз в месяц.\n'
    ),
    'moderate': (
        '• Смягчите разгон: нажимайте газ не более чем на 70 %.\n'
        '• Тормозите заранее, оставляя до впереди идущего авто 2 секунды (время между его проездом ориентира и вашим).\n'
        '• Включите Eco‑режим и меньше перестраивайтесь.\n'
    ),
    'aggressive': (
        '• Снизьте среднюю скорость до разрешённого лимита.\n'
        '• Держите дистанцию до впереди идущего автомобиля не менее 4 секунд (время между его проездом ориентира и вашим).\n'
        '• Избегайте рывков и резких манёвров • Запишитесь на курс безопасного вождения.\n'
    )
}


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
        User, on_delete=models.CASCADE, verbose_name='Пользователь',
        related_name='trips'
    )
    start_date_time = models.DateTimeField('Дата и время начала')
    end_date_time = models.DateTimeField('Дата и время окончания')
    sensor_data_file = models.FileField(
        'Файл с данными с датчиков', upload_to='sensor_data'
    )


class TripAnalysis(models.Model):
    """Анализ поездки."""
    trip = models.OneToOneField(
        Trip, on_delete=models.CASCADE, verbose_name='Поездка'
    )
    avg_speed = models.FloatField('Средняя скорость (км/ч)')
    distance = models.FloatField('Пройденное расстояние (км)')
    hard_brakes = models.IntegerField('Частота резких торможений')
    hard_accels = models.IntegerField('Частота резких ускорений')
    sharp_turns = models.IntegerField('Число резких маневров')
    avg_gyro_mag = models.FloatField('Средняя угловая скорость')
    trip_duration = models.FloatField('Длительность поездки')


class DrivingStyle(models.Model):
    """Оценка стиля вождения."""
    analysis = models.OneToOneField(
        TripAnalysis, on_delete=models.CASCADE, verbose_name='Анализ поездки'
    )
    category = models.CharField('Категория стиля', choices=CATEGORIES)
    recommendations = models.TextField('Рекомендации')
    timestamp = models.DateTimeField(
        'Дата и время создания оценки', default=timezone.now
    )

    def add_recommendations(self):
        """Сохранение рекомендации исходя из категории."""
        self.recommendations = RECOMMENDATIONS.get(self.category)
        self.save()


class UserDrivingProfile(models.Model):
    """Профиль вождения пользователя."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    total_trips = models.IntegerField('Общее число поездок')
    avg_speed = models.FloatField('Средняя скорость (км/ч)')
    total_distance = models.FloatField('Пройденное расстояние (км)')
    avg_brakes = models.FloatField('Среднее число резких торможений')
    avg_accels = models.FloatField('Среднее число резких ускорений')
    avg_sharp_turns = models.FloatField('Среднее число резких маневров')
    avg_gyro_mag = models.FloatField('Средняя угловая скорость')
    overall_category = models.CharField('Общая категория стиля', max_length=50)
