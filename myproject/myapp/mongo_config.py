# mongo_config.py
from mongoengine import connect
from django.conf import settings

def connect_to_mongo():
    connect(
        db=settings.MONGO_DATABASE_NAME,
        username=settings.MONGO_USERNAME,
        password=settings.MONGO_PASSWORD,
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT
    )