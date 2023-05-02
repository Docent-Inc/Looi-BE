FROM python:3.9

WORKDIR /app

COPY main.py /app/
COPY app /app/app/
COPY .env /app/
COPY requirements.txt /app/
# COPY alembic.ini /app/
# COPY alembic /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

# 적절한 워커 수를 설정한 후 Gunicorn을 실행하십시오. 예를 들어, 4개의 워커를 사용하려면:
# CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--timeout", "120"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]