FROM python:3.12

WORKDIR /app

COPY service/requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "main:app", "-c", "gunicorn.config.py"]
