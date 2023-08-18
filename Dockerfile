FROM python:3.9

WORKDIR /app

COPY main.py /app/
COPY app /app/app/
COPY .env /app/
COPY requirements.txt /app/
COPY gunicorn_logging.conf /app/
COPY app/core/formatter_with_localtime.py /app/app/core/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

