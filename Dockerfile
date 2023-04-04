#
FROM python:3.9

#
WORKDIR /app

#
COPY main.py /app/
COPY app /app/app/
COPY requirements.txt /app/

#
RUN pip install --no-cache-dir -r requirements.txt

#
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]