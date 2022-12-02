import os
import json
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
basedir = Path(__file__).resolve().parent.parent

config = None

if not os.path.exists(basedir.joinpath('config.json')):
    import secrets

    with open(basedir.joinpath('config.json'), 'w') as config_file:

        config = {
            'SECRET_KEY': secrets.token_hex(),
            'DB_URI': 'mysql://localhost:3306/dividendshub'
        }

        json.dump(config, config_file)
else:
    with open(basedir.joinpath('config.json')) as config_file:
        config = json.load(config_file)


class Config(object):
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
