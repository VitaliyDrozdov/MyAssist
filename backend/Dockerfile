
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
COPY ../data /app/data
CMD ["gunicorn", "--bind", "0.0.0.0:7500", "foodgram.wsgi"] 