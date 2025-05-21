# SmartDriveAI_Backend

## Локальный запуск в Docker
Находясь в корне проекта, выполнить команду для запуска сети контейнеров
```
docker compose up
```
В новом терминале выполнить команду по сбору статики Django
```
docker compose exec backend python manage.py collectstatic
```
Копирование статики в папку /backend_static/static/:
```
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```
Применение миграций:
docker compose exec backend python manage.py migrate

Документация API доступна по адресу `http://127.0.0.1:8080/docs/`.
