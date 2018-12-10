#encoding:utf-8

from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import request, current_app, session
from . import db, login_manager
from sqlalchemy.sql import func
from random import random

#Creer une classe pour croiser reponses et utilisateurs

class Cohorte(db.Model):
    __tablename__ = 'cohorte'
    id_cohorte = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    etablissement = db.Column(db.String(64))
    # section - UFR par exemple,...
    section = db.Column(db.String(32))
    niveau_academique = db.Column(db.String(32))
    annee_universitaire = db.Column(db.String(32))
    semestre = db.Column(db.String(32))
    responsable_cohorte = db.Column(db.String(64))

    def __repr__(self):
        return "<cohorte('%s', '%s', '%s', '%s', '%s', '%s', '%s')>" \
        % (self.id_cohorte, self.etablissement, self.section, self.niveau_academique, \
        self.annee_universitaire, self.semestre, self.responsable_cohorte)



class Groupe(db.Model):
    __tablename__ = 'groupe'
    id_groupe = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    nom_groupe = db.Column(db.String(32))
    cohorte_id = db.Column(db.Integer, db.ForeignKey("cohorte.id_cohorte"), nullable=False)
    responsable_groupe = db.Column(db.String(64))    
    Cohorte = db.relationship("Cohorte", foreign_keys=[cohorte_id])

    def __repr__(self):
        return "<groupe('%s', '%s', '%s', '%s')>" \
        % (self.id_groupe, self.nom_groupe, self.cohorte_id, self.responsable_groupe)



class Utilisateur(UserMixin, db.Model):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), nullable=False, unique=True, index=True)
    username = db.Column(db.String(64), nullable=False, index=True)
    is_admin = db.Column(db.Boolean)
    password_hash = db.Column(db.String(128))
    nom = db.Column(db.String(64), index=True)
    prenom = db.Column(db.String(64))
    premiere_inscription = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    groupe_id = db.Column(db.Integer, db.ForeignKey("groupe.id_groupe"))
    nb_sessions = db.Column(db.Integer, default=0)

    Groupe = db.relationship("Groupe", foreign_keys=[groupe_id])
    niveaux_diff = db.relationship("Difficulte", secondary='predictions_utilisateur_difficultes')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


    def __init__(self, **kwargs):
        super(Utilisateur, self).__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()


    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        _hash = self.avatar_hash or \
            hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=_hash, size=size, default=default, rating=rating)


    def __repr__(self):
        return "<utilisateur('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" \
        % (self.id, self.email, self.username, self.is_admin, self.password_hash, self.nom, self.prenom, \
        self.premiere_inscription, self.avatar_hash, self.nb_sessions, self.groupe_id)

@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))




# Mieux utiliser les classes : 
# créer une classe générique pour tous les types de question possibles, et ensuite relier.
class Phrase(db.Model):
    __tablename__ = 'phrase'
    id_phrase = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True, index=True)
    debut_phrase = db.Column(db.String(512))
    debut_mot_erreur = db.Column(db.String(64))
    element_reponse = db.Column(db.String(64))
    fin_mot_erreur = db.Column(db.String(64))
    fin_phrase = db.Column(db.String(512))
    difficulte_id = db.Column(db.Integer, db.ForeignKey("difficulte.id_difficulte"), nullable=False, index=True)
    ouvrage_id = db.Column(db.Integer, db.ForeignKey("ouvrage.id_ouvrage"), nullable=False)
    id_phrase_ds_ouvrage = db.Column(db.Integer)
    # corpus - Si la phrase appartient à un corpus particulier : histoire, droit, ...
    corpus = db.Column(db.String(32))
    #A convertir en views?    
    #nb_reponses = db.Column(db.Integer, default=0)
    #nb_reponses_correctes = db.Column(db.Integer, default=0)
    #Le statut peut être "OK", "En évaluation", "A revoir", "Ecartée"
    statut = db.Column(db.String(14), default = "En évaluation")

    Difficulte = db.relationship("Difficulte", foreign_keys=[difficulte_id])
    Ouvrage = db.relationship("Ouvrage", foreign_keys=[ouvrage_id])


    def __repr__(self):
        return "<phrase('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % \
        (self.id_phrase, self.debut_phrase, self.debut_mot_erreur, self.element_reponse, self.fin_mot_erreur, \
        self.fin_phrase, self.difficulte_id, self.ouvrage_id, self.corpus, self.id_phrase_ds_ouvrage)


class Ouvrage(db.Model):
    __tablename__ = 'ouvrage'
    id_ouvrage = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    nom_auteur = db.Column(db.String(64))
    nom_oeuvre = db.Column(db.String(128), unique=True)
    annee_oeuvre = db.Column(db.String(32))

    def __repr__(self):
        return "<ouvrage('%s', '%s', '%s', '%s')>" % \
        (self.id_ouvrage, self.nom_auteur, self.nom_oeuvre, self.annee_oeuvre)


class Difficulte(db.Model):
    __tablename__ = "difficulte"
    id_difficulte = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True, index=True)
    # priorite_difficulte - Classement du degré de priorité de la difficulté (subjectif?)
    priorite_difficulte = db.Column(db.Integer)
    # rang_difficulte - Déterminé par le taux de succès des étudiants
    rang_difficulte = db.Column(db.Integer)
    # type_difficulte - Trois niveaux de hiérarchie
    type_difficulte = db.Column(db.String(64))
    type_difficulte2 = db.Column(db.String(64))
    type_difficulte3 = db.Column(db.String(64))
    nature_mot_difficulte = db.Column(db.String(32))
    fonction_mot_difficulte = db.Column(db.String(32))
    frequence_difficulte = db.Column(db.Float)
    nb_questions = db.Column(db.Integer)

    vers_utilisateurs = db.relationship("Utilisateur", secondary='predictions_utilisateur_difficultes')

    def __repr__(self):
        return "<difficulte('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % \
        (self.id_difficulte, self.priorite_difficulte, self.rang_difficulte, self.type_difficulte, \
        self.type_difficulte2, self.type_difficulte3, self.nature_mot_difficulte, self.fonction_mot_difficulte)


class Test(db.Model):
    __tablename__ = "test"
    id_test = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"))
    heure_debut = db.Column(db.DateTime, default=datetime.utcnow)
    heure_fin = db.Column(db.DateTime)
    # controle - Indique si le test a été passé sous surveillance ou en autonomie
    controle = db.Column(db.Boolean, default=False)

    Utilisateur = db.relationship("Utilisateur", foreign_keys=[utilisateur_id])


    def __init__(self, user_id):
        self.utilisateur_id = user_id
        
        db.session.add(self)


    def __repr__(self):
        return "<test('%s', '%s', '%s', '%s', '%s')>" % \
        (self.id_test, self.utilisateur_id, self.heure_debut, self.heure_fin, self.controle)
        
 


class Reponse(db.Model):
    __tablename__ = "reponse"
    id_reponse = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("test.id_test"), index=True)
    phrase_id = db.Column(db.Integer, db.ForeignKey("phrase.id_phrase"), index=True)
    contenu_reponse = db.Column(db.String(32))
    duree = db.Column(db.Float)

    Test = db.relationship("Test", foreign_keys=[test_id])
    Phrase = db.relationship("Phrase", foreign_keys=[phrase_id])

    def __repr__(self):
        return "<reponse('%s', '%s', '%s', '%s', '%s')>" % \
        (self.id_reponse, self.test_id, self.phrase_id, self.contenu_reponse, self.duree)


# Répertoire de types de test, permet de configurer le test initial (durée, corpora...)
class TypeTest(db.Model):
    __tablename__ = "type_test"
    id_type_test = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    #Durée du test en minutes
    duree = db.Column(db.Integer)
    #Nombre max de questions
    nb_questions = db.Column(db.Integer)
    #Liste en json des corpora à interroger
    corpora = db.Column(db.String(64))

    def __repr__(self):
        return "<type_test('%s', '%s', '%s', '%s')>" % (self.id_type_test, self.duree, self.nb_questions, self.corpora)


class StatsPhrases(db.Model):
    __tablename__ = "stats_phrases"
    phrase_id = db.Column(db.Integer, db.ForeignKey("phrase.id_phrase"), nullable=False, primary_key=True)
    nb_reponses = db.Column(db.Integer)
    # Le centile dans lequel se trouve la phrase par rapport à la DB. 
    # Diffère de la p-value dans la mesure où le corpus de phrases est divisé de manière linéaire.
    centile_diff = db.Column(db.Integer)
    #p-value = proportion d'étudiants ayant répondu correctement à la question, aussi appelée Item Difficulty Index.
    p_value = db.Column(db.Float)
    #Discrimination_index: indique la correlation d'une réponse positive à la question avec l’appartenance au groupe maîtrisant l'item.
    # Attention, a une correlation avec le tx de difficulté.
    # Une version est calculée pour chaque niveau de définition de difficulté
    # Un score > à 0.4: TB ; OK si > à 0.3;  mauvais en dessous de 0.19
    discrimination_index_niv3 = db.Column(db.Float)
    discrimination_index_niv2 = db.Column(db.Float)
    discrimination_index_niv1 = db.Column(db.Float)
    #Coefficient de discrimination "point biserial". Permettrait de mesurer le pouvoir prédicitf de l'item. 
    # Combine la mesure de la pertinence de la phrase poru la difficulté et de son niveau de difficulté
    coef_discr_pbis = db.Column(db.Float)
    # Coefficient de discrimination "biserial correlation". Mesure l'efficacité de la phrase à l'intérieur du critère. 
    # "estimate of the well-known Pearson product-moment correlation between the criterion score and the hypothesized item continuum 
    # when the item is dichotomized into right and wrong"
    coef_discr_bis_corr = db.Column(db.Float)
    #Standard error of mesurement
    sem = db.Column(db.Float)
    #Intervalle de confiance
    int_conf = db.Column(db.Float)
    #IRT a1 - Discrimination
    irt_a1 = db.Column(db.Float, default=1)
    #IRT d - Difficulty, aussi appelé b. Mesuré sur la même échelle que Théta
    irt_d = db.Column(db.Float)
    #IRT g - Pseudo-guessing, aussi appelé c. Probabilité de trouver la bonne réponse par chance
    irt_g = db.Column(db.Float, default=0)
    #IRT u - Upper asymptote. Probabilité que des individus compétents puissent répondre incorrectement.
    irt_u = db.Column(db.Float,  default=1)
    #irt_mean = db.Column(db.Float)

    Phrase = db.relationship("Phrase", foreign_keys=[phrase_id])


class StatsDifficultes(db.Model):
    __tablename__ = "stats_difficultes"
    difficulte_id = db.Column(db.Integer, db.ForeignKey("difficulte.id_difficulte"), nullable=False, primary_key=True)
    #Le rang de difficulté de la difficulté dnas tout le corpus ( 1= item le plus difficile). Fonder sur la p-value ou le discrimination index? Plutôt le second.
    rang_diff = db.Column(db.Integer)
    #p-value = proportion d'étudiants ayant répondu correctement à la difficulte, aussi appelée Item Difficulty Index.
    p_value = db.Column(db.Float)
    #Discrimination_index: indique le caractère plus ou moins informatif d'une difficulté sur le niveau global.
    discrimination_index = db.Column(db.Float)
    #Coefficient de discrimination "point biserial". Permettrait de mesurer le pouvoir prédicitf de l'item. Combine la mesure de la pertinence de la phrase poru la difficulté et de son niveau de difficulté
    coef_discr_pbis = db.Column(db.Float)
    #Coefficient de discrimination "biserial correlation". Mesure l'efficacité de la phrase à l'intérieur du critère. "estimate of the well-known Pearson product-moment correlation between the criterion score and the hypothesized item continuum when the item is dichotomized into right and wrong"
    coef_discr_bis_corr = db.Column(db.Float)
    #Cronbach’s Alpha - à mettre aussi à l'échelle des phrases?
    cr_alpha = db.Column(db.Float)
    #Standard error of mesurement
    sem = db.Column(db.Float)
    #Intervalle de cofiance
    int_conf = db.Column(db.Float)
    irt_mean = db.Column(db.Float)

    Difficulte = db.relationship("Difficulte", foreign_keys=[difficulte_id])


class StatsTests(db.Model):
    __tablename__ = "stats_tests"
    test_id = db.Column(db.Integer, db.ForeignKey("test.id_test"), nullable=False, primary_key=True)
    #Cronbach's Alpha
    cr_alpha = db.Column(db.Float)
    #Standard error of mesurement
    sem = db.Column(db.Float)
    #Intervalle de cofiance
    int_conf = db.Column(db.Float)

    Test = db.relationship("Test", foreign_keys=[test_id])


class LienUtilisateursDifficultes(db.Model):
    __tablename__ = 'predictions_utilisateur_difficultes'
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), primary_key=True)
    difficulte_id = db.Column(db.Integer, db.ForeignKey("difficulte.id_difficulte"), primary_key=True)
    niveau = db.Column(db.Float)

    Difficulte = db.relationship("Difficulte", foreign_keys=[difficulte_id])
    Utilisateur = db.relationship("Utilisateur", foreign_keys=[utilisateur_id])

    
class CovMatrix(db.Model):
    """on donne commme indexs les identités des difficultés."""
    __tablename__ = 'covariance_matrix'
    diff_row = db.Column(db.String(4), primary_key=True)
    diff_col = db.Column(db.String(4), primary_key=True)
    valeur = db.Column(db.Float)
    
