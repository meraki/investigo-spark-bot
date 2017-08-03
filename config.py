import os


class Config(object):
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DEBUG = False
    SECRET_KEY = os.environ['SECRET_KEY']
    DATABASE_URL = os.environ['DATABASE_URL']
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    TROPO_API_KEY_TEXT = os.environ.get('TROPO_API_KEY_TEXT', "TEXT TOKEN NOT PROVIDED")
    TROPO_API_KEY_VOICE = os.environ.get('TROPO_API_KEY_VOICE', "VOICE TOKEN NOT PROVIDED")
    SPARK_TOKEN = os.environ.get('SPARK_TOKEN', "TOKEN-NOT-PROVIDED")
    ON_CISCO_NETWORK = os.environ.get('ON_CISCO_NETWORK', False)
    NOTIFICATION_SMS_PHONE_NUMBER = os.environ.get('NOTIFICATION_SMS_PHONE_NUMBER', False)
    SPARK_DEFAULT_ROOM_ID = os.environ.get('SPARK_DEFAULT_ROOM_ID', False)
    SMS_ENABLED = bool(os.environ.get('SMS_ENABLED', False))
    SHOW_WEB_LINK = bool(os.environ.get('SHOW_WEB_LINK', False))
    ADMIN_NAME = os.environ.get('ADMIN_NAME', '')
    MERAKI_VALIDATOR_TOKEN = os.environ.get('MERAKI_VALIDATOR', "TOKEN-NOT-PROVIDED")

    # Application threads. A common general assumption is
    # using 2 per available processor cores - to handle
    # incoming requests using one and performing background
    # operations using the other.
    THREADS_PER_PAGE = 2


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
