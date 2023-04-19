FROM python:3.9

WORKDIR /app

COPY main.py /app/
COPY app /app/app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Gunicorn을 설치합니다.
RUN pip install gunicorn

ENV PYTHONUNBUFFERED=1

# 적절한 워커 수를 설정한 후 Gunicorn을 실행하십시오. 예를 들어, 4개의 워커를 사용하려면:
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
