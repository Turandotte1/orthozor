#! encoding: utf-8
#! python3


#from flask import Flask, render_template, redirect, url_for, session

from flask import session, render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from . import questionnaire
from ..models import Test, Phrase, Reponse, Ouvrage, Difficulte, Utilisateur, Cohorte, Groupe
from .forms import QuestionForm
from app import db  # , mab
from datetime import datetime
from time import time
from datetime import datetime
import json
from random import random
#from flask_mab import reward_endpt, choose_arm
from app.mirt import next_question, get_thetas


# On peut aussi imaginer divers types de questions. Essayer aussi le type StringField


@questionnaire.route('/questions', methods=['GET', 'POST'])
@login_required
def questions():

    # print(request.referrer)
    # Penser à réintégrer la condition /test/questions not in request.referrer
    # if '0.0.0.0:5000' not in request.referrer:
    #    print("Nouvelle entrée dans le système 'questions' detectée.")
    #    session.clear()
    # Verification de l'intégrité de la question
    print("Dictionnaire session:", session.__dict__)
    print("Objet session:", session)

    if 'questions_posées' not in session:
        print("Test initialisé")
        # session.clear()
        jeu = Test(current_user.get_id())
        db.session.add(jeu)
        db.session.commit()
        session['id_test'] = jeu.id_test
        session['questions_posées'] = []
        # Réponses évaluées, 1 ou 0
        session['reponses_eval'] = []
        session['durees_rep'] = []
        # La liste // à reponses_eval des index de difficultés concernés
        session['id_ difficultes'] = []
        session['question'] = next_question(
            session['questions_posées'], session['reponses_eval'])
        #session['dic_question'] = dic_question

    dic_question = Phrase.query.get(session['question']).__dict__

    # Si plus de question, on passe au bilan
    if session['question'] == None:
        # Insertion de l'heure de fin du test
        db.session.query(Test).filter(Test.id_test == session['id_test']).update(
            {'heure_fin': datetime.utcnow()})
        db.session.commit()
        return redirect(url_for('questionnaire.bilan'))

    # Récupération des références de l'oeuvre
    data_oeuvre = Ouvrage.query.filter(
        Ouvrage.id_ouvrage == dic_question['ouvrage_id']).first()

    form = QuestionForm()

    if form.validate_on_submit():

        print("Entrée dans validate")
        # Le timing pourrait être amélioré, mais donne une idée.
        _dr = session['durees_rep']
        _dr.append(round(time()-session['debut_q'], 3))
        session['durees_rep'] = _dr

        dic_question = Phrase.query.get(session['question']).__dict__

        contenu_reponse = form.answer.data.strip()

        # Insertion dans la DB
        rep = Reponse(duree=session['durees_rep'][-1], test_id=session['id_test'],
                      phrase_id=session['question'], contenu_reponse=contenu_reponse)
        db.session.add(rep)

        # MAJ des données de la session
        #session['reponses_correctes'] = []
        _qp = session['questions_posées']
        _qp.append(session['question'])
        session['questions_posées'] = _qp

        # Evluation de la réponse
        ok_ou_non = int(dic_question["element_reponse"] == contenu_reponse)
        # Réponses évaluées, 1 ou 0
        _re = session['reponses_eval']
        _re.append(ok_ou_non)
        session['reponses_eval'] = _re
        # On ajoute l'id de la difficulté à la liste
        _df = session['id_ difficultes']
        _df.append(dic_question["difficulte_id"])
        session['id_ difficultes'] = _df

        print("Avant next q")

        # the user answered the question, advance to the next question
        session['question'] = next_question(
            questions=session['questions_posées'], reponses=session['reponses_eval'])
        #dic_question = db.session.query(Phrase).get(session['question'])
        #session['dic_question'] = dic_question
        return redirect(url_for('questionnaire.questions'))

    session['debut_q'] = time()
    # Si pas de validation, on repose la question

    return render_template('questionnaire/question.html',
                           debut_phrase=dic_question['debut_phrase'],
                           debut_mot_erreur=dic_question['debut_mot_erreur'],
                           fin_mot_erreur=dic_question['fin_mot_erreur'],
                           fin_phrase=dic_question['fin_phrase'],
                           oeuvre=data_oeuvre.nom_oeuvre,
                           auteur=data_oeuvre.nom_auteur,
                           annee=data_oeuvre.annee_oeuvre,
                           form=form)


@questionnaire.route('/bilan', methods=['GET'])
# @mab.reward_endpt("image_score_freq", reward_val=0)
# @mab.reward_endpt("image_score_duree", reward_val=0)
@login_required
def bilan():
    if 'id_test' not in session:
        # if we have no question in the session we go to the start page
        return redirect(url_for('orthozor.index'))

    donnees = dict()

    # ******************************
    # Nouveau système avec mirtcat

    # ******************************

    # Score général
    ##############
    donnees['nb_total_reponses'] = len(session['reponses_eval'])
    donnees['nb_reponses_correctes'] = session['reponses_eval'].count(1)

    # Histogrammes : catégories de rang 2
    ####################################
    # Génération d'un set d'étiquettes de difficultés rassemblant diff de rang 1 et 2
    # On recueille l'id, la diff de rang 1 et le nom agrégeant diffs de rang 1 et 2
    set_diff_2 = [(x[0], x[1], ' - '.join(x[1:])) if x[2] != '' else (x[0], x[1]) for x in db.session.query(
        Difficulte.id_difficulte, Difficulte.type_difficulte, Difficulte.type_difficulte2).distinct().all()]

    lst_diff_r2 = []
    # print(set_diff_2)
    for id_d, _, nom in set_diff_2:

        # On compte le nombre total de réponses
        nb_tot_rep = session["id_ difficultes"].count(id_d)

        # Si la sous-catégorie n'a pas été testée, on la saute
        if nb_tot_rep == 0:
            continue

        # On compte le nombre de bonnes réponses
        nb_bonnes_rep = len([x for x in zip(
            session["id_ difficultes"], session["reponses_eval"]) if x[0] == id_d and x[1] == 1])

        # Ajout à la liste et normalisation sur 100
        lst_diff_r2.append((nom, nb_bonnes_rep / nb_tot_rep * 100))

    # Classement par score et jsonification
    lst_diff_r2 = sorted(lst_diff_r2, key=lambda x: x[1], reverse=True)
    donnees['data_diff_2'] = json.dumps([x[1] for x in lst_diff_r2])
    donnees['etiq_diff_2'] = json.dumps([x[0] for x in lst_diff_r2])

    # Radar:  difficultés de rang 1
    ##############################
    set_diff_1 = [x[1] for x in set_diff_2]

    lst_diff_r1 = []
    lst_diff_r1_cohorte = []

    # A récupérer à la connexion
    # Récup no cohorte
    no_cohorte = db.session.query(Cohorte.id_cohorte).join(Groupe).join(
        Utilisateur).filter(Groupe.id_groupe == current_user.groupe_id).first()[0]
    #print("No cohorte: {}".format(no_cohorte))

    for item in set_diff_1:
        #print("\n", item)
        # On compte le nombre total de réponses de l'individu
        nb_tot_rep = len(session["reponses_eval"])

        # On compte le nombre total de réponses de la cohorte
        nb_tot_rep_cohorte = db.session.query(Reponse).join(Phrase).join(Difficulte).join(Test).join(Utilisateur).join(Groupe).join(Cohorte). \
            filter(Cohorte.id_cohorte == no_cohorte). \
            filter(Difficulte.type_difficulte == item).count()
        #print("Nb tot rep cohorte: {}".format(nb_tot_rep_cohorte))

        # On compte le nombre de bonnes réponses de l'individu
        nb_bonnes_rep = session["reponses_eval"].count(1)

        # On compte le nombre de bonnes réponses de la cohorte
        nb_bonnes_rep_cohorte = db.session.query(Reponse).join(Phrase).join(Difficulte).join(Test).join(Utilisateur).join(Groupe).join(Cohorte). \
            filter(Cohorte.id_cohorte == no_cohorte). \
            filter(Difficulte.type_difficulte == item). \
            filter(Reponse.contenu_reponse == Phrase.element_reponse).count()
        #print("Nb bonnes rep cohorte: {}".format(nb_bonnes_rep_cohorte))

        # On évite la division par 0
        if nb_tot_rep == 0:
            nb_tot_rep = 1
        if nb_tot_rep_cohorte == 0:
            nb_tot_rep_cohorte = 1

        # Ajout à la liste et normalisation sur 100
        lst_diff_r1.append(nb_bonnes_rep / nb_tot_rep * 100)
        lst_diff_r1_cohorte.append(
            nb_bonnes_rep_cohorte / nb_tot_rep_cohorte * 100)

    donnees['etiq_diff1'] = json.dumps(set_diff_1)
    donnees['data_diff_1'] = json.dumps(lst_diff_r1)
    donnees['data_diff_1_cohorte'] = json.dumps(lst_diff_r1_cohorte)

    # Récupération des phrases corrigées (filtrage sur erreurs)
    phrases_corr = db.session.query(Phrase).join(Reponse). \
        filter(Reponse.test_id == session['id_test']). \
        filter(Reponse.contenu_reponse != Phrase.element_reponse).all()
    #print(session['id_test'], "Phrases à corriger: ", len(phrases_corr))
    # print(phrases_corr)

    # Envoi des données à Flask-MABandits
    # if donnees['nb_total_reponses'] != 0:

    # bilan.rewards = [
    # ("image_score_freq", ((donnees['nb_reponses_correctes'] / donnees['nb_total_reponses'] ) * 100)),
    # ("image_score_duree", ((donnees['nb_reponses_correctes'] / donnees['nb_total_reponses'] ) * 100))]
    # print("Récompense activée")

    # Suppression de la clé id_test dans la session
    del session['id_test']
    # print(donnees)
    # print(session.__dict__)
    return render_template('questionnaire/bilan.html', donnees=donnees, phrases_corr=phrases_corr)


@questionnaire.route('/clear')
def clearsession():
    # Clear the session
    session.clear()
    # Redirect the user to the main page
    return redirect(url_for('orthozor.index'))
