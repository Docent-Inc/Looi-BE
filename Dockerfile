FROM python:3.9

WORKDIR /app

COPY main.py /app/
COPY app /app/app/
COPY .env /app/
COPY requirements.txt /app/
COPY gunicorn_logging.conf /app/
COPY app/core/formatter_with_localtime.py /app/app/core/
# COPY alembic.ini /app/
# COPY alembic /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

# CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--timeout", "300", "--log-config", "gunicorn_logging.conf"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

