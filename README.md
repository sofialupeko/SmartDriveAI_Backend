# SmartDriveAI_Backend

## Локальный запуск в Docker
Перейти в директорию с проектом:
```
cd SmartDriveAI_Backend
```
Запустить сеть контейнеров в фоновом режиме:
```
docker compose up -d
```
Если код меняется контейнеры нужно пересобрать и запустить:
```
docker compose up --build -d
```

# При первом запуске
Сбор статики Django:
```
docker compose exec backend python manage.py collectstatic
```
Копирование статики в папку /backend_static/static/:
```
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```
Применение миграций:
```
docker compose exec backend python manage.py migrate
```

Документация API доступна по адресу `http://127.0.0.1:8000/docs/`.
