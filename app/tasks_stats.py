#!encoding: utf-8
#!python3

from app import db
from app.models import Phrase, Reponse, StatsPhrases


# STATISTIQUES
# ************


# A supprimer - plus efficace de créer des tâches séparées dans le contexte de Celery
# On lance tous les calculs au startup
def toutes_stats():
    a = time()
    calcul_p_value()
    print("p-value: ", time() - a, " s.")
    calcul_centile()
    print("centile: ", time() - a, " s.")
    calcul_discrimination_index()
    print("discrimination index: ", time() - a, " s.")


def calcul_p_value():
    """Calcule la p-value pour l'ensemble des questions. p-value = proportion d'étudiants ayant répondu correctement à la question, aussi appelée Item Difficulty Index."""
    for row in db.session.query(Phrase):
        nb_rep_correctes = db.session.query(Phrase).join(Reponse).filter(
            Reponse.phrase_id == row.id_phrase).filter(Reponse.contenu_reponse == Phrase.element_reponse).count()
        nb_total_rep = db.session.query(Reponse).filter(
            Reponse.phrase_id == row.id_phrase).count()
        #print(row.id_phrase, nb_rep_correctes, nb_total_rep)
        # Pour éviter la division par zéro, on considère qu'il y a au moins une réponse
        if nb_total_rep == 0:
            nb_total_rep = 1
        data = StatsPhrases(phrase_id=row.id_phrase,
                            p_value=nb_rep_correctes / nb_total_rep, nb_reponses=nb_total_rep)
        # merge permet de faire un create or update
        db.session.merge(data)

    db.session.commit()

# Calcul du centile de difficulté


def calcul_centile():
    # """Remplit en bloc la colonne centile de difficulté dans Stats_phrase."""
        # On récupère la liste des index de phrase classés par p-value
    lst = [x[0] for x in sorted(db.session.query(
        Stats_phrases.phrase_id, Stats_phrases.p_value).all(), key=lambda x: x[1], reverse=True)]
    for item in range(len(lst)):
        data = Stats_phrases(phrase_id=lst[item], centile_diff=int(
            round(item/len(lst), 2)*100))
        # merge permet de faire un create or update
        db.session.merge(data)
    db.session.commit()


# Calcul du discrimination index
# A revoir: le calcul a lieu sur le score global, et on ne normalise pas en fonction du nombre de fois où la question a été présentée dans chaque groupe. Ne donne à ce stade qu'une approximation.
def calcul_discrimination_index():
    # Calcul des competences utilisateur
    liste_competences = []

    for utilisateur in [x for x, in db.session.query(Utilisateur.id).all()]:
        # Récupération de toutes les réponses
        reponses = db.session.query(Reponse).join(Test). \
            filter(Test.utilisateur_id == utilisateur)

        # Iteration sur les difficultes pour déterminer le niveau sur chaque difficulté
        for difficulte in [x for x, in db.session.query(Difficulte.id_difficulte).all()]:
            rep_concernees = reponses.join(Phrase).filter(
                Phrase.difficulte_id == difficulte)

            # On passe si la difficulté a eu moins de 3 réponses par l'étudiants
            if rep_concernees.count() < 3:
                continue
            # Calcul du score pour la difficulté
            score = rep_concernees.filter(
                Reponse.contenu_reponse == Phrase.element_reponse).count() / rep_concernees.count()
            liste_competences.append((utilisateur, difficulte, score))
            #print(utilisateur, difficulte, score)

    # Scoring des phrases
    for difficulte in db.session.query(Difficulte).all():
        # On détermine le niveau de la difficulté
        if difficulte.type_difficulte3 != "":
            niv_diff = 3
        elif difficulte.type_difficulte2 != "":
            niv_diff = 2
        else:
            niv_diff = 1

        lst_comp_loc = sorted(
            [x for x in liste_competences if x[1] == difficulte], key=lambda x: x[2])

        # Si moins de 10 personne dans le groupe de détermination des compétences: on continue
        # if len(lst_comp_loc) < 10:
        #	continue

        bons = [x[0] for x in lst_comp_loc if lst_comp_loc.index(
            x)/len(lst_comp_loc) >= 0.73]
        mauvais = [x[0] for x in lst_comp_loc if lst_comp_loc.index(
            x)/len(lst_comp_loc) >= 0.27]

        # Iteration sur les phrases concernés par la difficulté
        for phrase in db.session.query(Phrase).filter(Phrase.difficulte_id == difficulte.id_difficulte):
            # print(phrase)
            nb_bonnes_reponses_bons = db.session.query(Reponse).join(Test).filter(Reponse.contenu_reponse == phrase.element_reponse). \
                filter(Reponse.phrase_id == phrase.id_phrase). \
                filter(Test.utilisateur_id in bons).count()
            #print("Nb bonnes reponses bons", nb_bonnes_reponses_bons)
            nb_bonnes_reponses_mauvais = db.session.query(Reponse).join(Test).filter(Reponse.contenu_reponse == phrase.element_reponse). \
                filter(Reponse.phrase_id == phrase.id_phrase). \
                filter(Test.utilisateur_id in mauvais).count()
            #print("Nb bonnes reponses mauvais", nb_bonnes_reponses_mauvais)
            nb_reponses_bons = db.session.query(Reponse).join(Test). \
                filter(Test.utilisateur_id in bons).count()
            nb_reponses_mauvais = db.session.query(Reponse).join(Test). \
                filter(Test.utilisateur_id in mauvais).count()
            # On evite la division par zéro (utile seulement en dev si moins de dix persones dans la DB):
            if nb_reponses_mauvais == 0 or nb_reponses_bons == 0:
                continue

            # ATTENTION: dans la mesure où tout le monde ne passe pas le même test, le calcul du discrimination index ne correspond pas à la pratique canonique
            discrimination_index_phrase = (nb_bonnes_reponses_bons / nb_reponses_bons) - (
                nb_bonnes_reponses_mauvais / nb_reponses_mauvais)

            # Insertion du discrimination index

            # ON fait un dictionnaire pour indiquer quel niveau de difficulté on est en trin de traiter
            if niv_diff == 1:
                data = Stats_phrases(
                    phrase_id=phrase.id_phrase, discrimination_index_niv1=discrimination_index_phrase)
            elif niv_diff == 2:
                data = Stats_phrases(
                    phrase_id=phrase.id_phrase, discrimination_index_niv2=discrimination_index_phrase)
            else:
                data = Stats_phrases(
                    phrase_id=phrase.id_phrase, discrimination_index_niv3=discrimination_index_phrase)

            # merge permet de faire un create or update
            db.session.merge(data)
    db.session.commit()


# Calcul du coefficient de discrimination "point biserial" (comment la difficulté d'un item est reliée au score global
def point_biserial(id_question):
    # Calcul median de score des étudiants ayant répondu correctement

    # Recuperation de la liste de scores - attention, on tient compte de l'ensemble des réponses données par l'individu sans découper par tests
    lst_scores = []
    for _id in [x[0] for x in db.session.query(Utilisateur.id).all()]:
        score = db.session.query(Reponse).join(Test).join(Utilisateur).join(Phrase). \
            filter(Utilisateur.id == _id). \
            filter(Reponse.contenu_reponse == Phrase.element_reponse).count() / \
            db.session.query(Reponse).join(Test).join(Utilisateur). \
            filter(Utilisateur.id == _id). \
            count()
        lst_scores.append(score)
        print(score)
