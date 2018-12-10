#! encoding: utf-8
#! python3

import os
from flask import Flask, session, current_app
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_admin import Admin
from flask_redis import Redis
from flask_admin.contrib import rediscli
from app.models_admin import UserView, OrthozorModelView
from config import config, Config
from flaskext.markdown import Markdown
from app.bandits_en_cours import image_score_bandit_freq, image_score_bandit_duree
#from flask_mab import BanditMiddleware
from celery import Celery



db = SQLAlchemy()
migrate = Migrate()
redis = Redis()
sess = Session()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
bootstrap = Bootstrap()
admin = Admin(name='Orthozor', template_mode='bootstrap3', url='/admin')
#mab = BanditMiddleware()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

@celery.task()
def add_together(a, b):
    return a + b


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    redis.init_app(app)
    sess.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    admin.init_app(app)
    #mab.init_app(app)
    Markdown(app)
    celery.conf.update(app.config)

    
    
    #Flask-MAB
    #app.add_bandit('image_score_freq', image_score_bandit_freq)
    #app.add_bandit('image_score_duree', image_score_bandit_duree)
    
    #Flask-admin
    from app.models import Utilisateur, Phrase, Cohorte, Groupe, Difficulte, Ouvrage, Reponse, Test, TypeTest, StatsPhrases
    admin.add_view(UserView(Utilisateur, db.session))
    admin.add_view(OrthozorModelView(Phrase, db.session))
    admin.add_view(OrthozorModelView(Cohorte, db.session))
    admin.add_view(OrthozorModelView(Groupe, db.session))
    admin.add_view(OrthozorModelView(Difficulte, db.session))
    admin.add_view(OrthozorModelView(Ouvrage, db.session))
    admin.add_view(OrthozorModelView(Test, db.session))
    admin.add_view(OrthozorModelView(Reponse, db.session))
    admin.add_view(OrthozorModelView(TypeTest, db.session))
    admin.add_view(OrthozorModelView(StatsPhrases, db.session))
    #admin.add_view(rediscli.RedisCli(Redis()))
    #admin.add_view(FileAdmin('/static/', name='Static Files'))
    
    
    from .orthozor import orthozor as orthozor_blueprint
    app.register_blueprint(orthozor_blueprint)
    
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .questionnaire import questionnaire as questionnaire_blueprint
    app.register_blueprint(questionnaire_blueprint, url_prefix='/test')
    
    #from .recompense import recompense as recompense_blueprint
    #app.register_blueprint(recompense_blueprint, url_prefix='/recompense')
    
    #from .admin import admin as admin_blueprint
    #app.register_blueprint(admin_blueprint, url_prefix='/administration')
    
    
    return app