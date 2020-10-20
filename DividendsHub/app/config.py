import os
import json

with open('/etc/config.json') as config_file:
    config = json.load(config_file)

class Config:
    SQLALCHEMY_DATABASE_URI = config.get('DB_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = config.get('SECRET_KEY')

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = config.get('MAIL_USERNAME')
    MAIL_PASSWORD = config.get('MAIL_PASSWORD')
    EMAIL = config.get('EMAIL')

    IEX_CLOUD_key = config.get('IEX_CLOUD_key')
    FINNHUB_key = config.get('FINNHUB_key')
