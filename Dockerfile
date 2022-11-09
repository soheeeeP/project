FROM python:3.10.2-slim

RUN apt-get update && apt-get -y install build-essential
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

COPY requirements.txt /app/
COPY . /app

RUN pip install -r requirements.txt
CMD ["sh", "-c",
    "python manage.py makemigrations\
     && python manage.py migrate --fake-initial\
      && python manage.py runserver 0.0.0.0:8000"]
