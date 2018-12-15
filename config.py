#!encoding: utf-8
#!python3


import os
from redis import from_url


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Multi-armed bandits
    MAB_STORAGE_ENGINE = 'JSONBanditStorage'
    MAB_STORAGE_OPTS = ('app/MABandits/bandit_storage.json',)

    # En secondes
    DUREE_TEST_MAX = 40 * 60
    # Nb max de questions par test
    NB_QUEST_MAX = os.environ.get('NB_QUEST_MAX') or 50
    NB_QUEST_MIN = os.environ.get('NB_QUEST_MAX') or 40

    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://127.0.0.1:6379'

    # Celery
    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

    # Flask-Session
    SESSION_TYPE = 'redis'
    SESSION_REDIS = from_url(REDIS_URL)
    #SESSION_USE_SIGNER = True
    SESSION_PERMANENT = False


class DevelopementConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 't0p s3cr3tahahah'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    # pass
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'developement': DevelopementConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopementConfig
}
