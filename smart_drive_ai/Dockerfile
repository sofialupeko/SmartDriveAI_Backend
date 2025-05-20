FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt --no-cache-dir

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "smart_drive_ai.wsgi"]
