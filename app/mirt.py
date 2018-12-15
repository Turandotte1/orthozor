#!encoding: utf-8
#!python 3

from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
import rpy2.robjects as robjects

from flask import current_app
from app.models import Utilisateur, Phrase, Groupe, Reponse, StatsPhrases, Test, Difficulte, StatsDifficultes, CovMatrix
from app import db
import pandas as pd
from random import random
from sqlalchemy import func


# Attention: le vecteru de thétas est hardcodé. Va bugguer si on ajoute des difficultes
# Passer le seuil minimum pour considérer un trst comme valide en variable d'environnement, de même que les paramètres pour MirtCAT.
# Passer aussi la liste des questions déjà vues = à ne pas présenter


# Imports R
mirt = importr("mirt")
parallel = importr("parallel")
mirtCAT = importr("mirtCAT")

pandas2ri.activate()


#c = robjects.r("c")

# Ne pas mettre de R en dehors de ce script


def generate_mirt(ordre_q_et_d=False):
    """Si ordre_q est vrai, renvoie à la fois l'objet mirt et l'ordre des questions."""

    # Verifier l'efficacité
    # Création d'un cluster pour accélérer les calculs
    mirt.mirtCluster(parallel.detectCores())

    # Extraction des id_difficulte pour chaque phrase
    ids_et_diffs_toutes_phrases = sorted(session.query(
        Phrase.id_phrase, Phrase.difficulte_id).all(), key=lambda x: x[0])

    def matrice_reponses(ids_et_diffs_toutes_phrases):
        """Revoie une matrice sous forme de DataFrame Pandas comportant l'ensemble des tests passés et les réponse à chaque question encodées en 1, 0, ou NaN."""

        # Récupération de toutes les réponses par test si l'utilisateur ne fait pas partie de la cohorte de test et si le test comporte au moins 30 questions
        matrice = {}

        for test in [x for x, in session.query(Test.id_test).join(Utilisateur).join(Groupe).
                     filter(Groupe.cohorte_id != 1).all()]:  # Filtrage de la cohorte de test

            bonnes_reponses = session.query(Reponse.phrase_id).join(Phrase). \
                filter(Reponse.test_id == test).  \
                filter(Reponse.contenu_reponse == Phrase.element_reponse).all()
            mauvaises_reponses = session.query(Reponse.phrase_id).join(Phrase). \
                filter(Reponse.test_id == test).  \
                filter(Reponse.contenu_reponse != Phrase.element_reponse).all()
            if len(bonnes_reponses + mauvaises_reponses) < 30:  # Filtrage des tests trop courts
                continue
            #print([x[0] for x in bonnes_reponses], [x[0] for x in mauvaises_reponses], "\n")

            lst = []
            # Itération sur la table Phrase
            for x, _ in ids_et_diffs_toutes_phrases:
                if x in set(x[0] for x in bonnes_reponses):
                    lst.append(1)
                elif x in set(x[0] for x in mauvaises_reponses):
                    lst.append(0)
                else:
                    lst.append(None)
            matrice[str(test)] = lst

            # print(reponses)

        df = pd.DataFrame(matrice).transpose()

        # On nomme les colonnes avec l'index des questions dans la DB
        df.columns = ["Q" + str(x[0]) for x in ids_et_diffs_toutes_phrases]

        # On supprime les lignes et les colonnes sans réponses
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(axis=0, how='all', inplace=True)

        return df

    df = matrice_reponses(ids_et_diffs_toutes_phrases)

    def generation_params_modele(df):
        """Reçoit une dataframe 'matrice_reponse' et renvoie un string comportant les paramètres de réponses pour l'administration de mirtCAT."""

        # Définition du modèle avec les traits latents
        modele_ = ""
        cov = []

        diff_traitées = []
        for id_q, diff in ids_et_diffs_toutes_phrases:
            if diff in diff_traitées:
                continue
            # Assignement des questions aux difficultés
            modele_ += "D" + str(diff) + " = " + ",".join([x for
                                                           x in list(df.columns) if int(x[1:]) == diff]) + "\n"
            # Def du calcul de covariance
            cov.append(str(diff))
            diff_traitées.append(diff)
        modele_ += "MEAN = D" + ",D".join(cov) + "\n"
        modele_ += "COV = D" + "*D".join(cov)
        # print(modele)
        modele = mirt.mirt_model(modele_, itemnames=list(df.columns))

        return modele

    modele = generation_params_modele(df)

    # Exploratoire
    #mod = mirt.mirt(df, 1, itemtype='Rasch', verbose=True)
    # Confirmatoire
    mod = mirt.mirt(df, modele, itemtype='2PL', method="SEM", verbose=True)

    # Pour arrêter le cluster:
    mirt.mirtCluster(remove=True)

    if ordre_q_et_d:
        # on passe cov qui est une liste des ids de difficultés, utile pour étiquerter ensuite les means et la matrice de covariance
        return (mod, (list(df.columns), cov))
    else:
        return mod


def integration_mirt_db(mirt_obj, ordre_q_et_d):

    ordre_q, ordre_d = ordre_q_et_d

    # MAJ stats questions
    for phrase in ordre_q:
        item = mirt.extract_item(mirt_obj, ordre_q.index(phrase)+1)
        item = [x for x in list(zip(list(item.slots["est"]), list(
            item.slots["par"]), list(item.slots["parnames"]))) if x[0] == True]
        phr = db.session.query(StatsPhrases).filter(
            StatsPhrases.phrase_id == phrase).one()
        phr.irt_a1 = [x[1] for x in item if "a" in x[2]][0]
        phr.irt_d = [x[1] for x in item if "d" in x[2]][0]
    db.session.commit()

    # MAJ stats difficultés

    coef = robjects.r["coef"]
    cfs = coef(mirt_obj, simplify=True)

    # Liste means
    means = list(zip(ordre_d, list(cfs[1])))
    for d, v in means:
        sd = StatsDifficultes()
        sd.difficulte_id = d
        sd.irt_mean = v
        old = db.session.query(StatsDifficultes).get(d)
        if old:
            db.session.merge(sd)
        else:
            db.session.add(sd)
            # db.session.query(StatsDifficultes).filter(StatsDifficultes.difficulte_id == d). \
        #update({StatsDifficultes.irt_mean: v})

    # Matrice de covariance
    cov = cfs[2]
    # itération sur la matrice
    for id_col in range(1, cov.ncol + 1):
        for id_row in range(1, cov.nrow + 1):
            old = db.session.query(CovMatrix).filter(
                CovMatrix.diff_col == ordre_d[id_col - 1]).filter(CovMatrix.diff_row == ordre_d[id_row - 1]).one_or_none()
            if old:
                old.valeur = cov.rx(id_row, id_col)[0]
            else:
                cv = CovMatrix(
                    diff_row=ordre_d[id_row - 1], diff_col=ordre_d[id_col - 1], valeur=cov.rx(id_row, id_col)[0])
                db.session.add(cv)
            #db.session.query(CovMatrix).update({CovMatrix.diff_row:ordre_d[id_row -1], CovMatrix.diff_col:ordre_d[id_col -1], CovMatrix.valeur:cov.rx(id_row, id_col)[0]})
            #cv = CovMatrix(diff_row = ordre_d[id_row -1], diff_col = ordre_d[id_col -1], valeur = cov.rx(id_row, id_col)[0])

    db.session.flush()
    db.session.commit()


def generer_objet_mirtcat(mirt_object):

    # print(mirt_object)
    # Initialisation cluster
    cl = parallel.makeCluster(parallel.detectCores())

    """Fonction qui créé un objet design pour le test adaptatif. Etablit notamment les thétas initiaux et les questions à ne pas poser.
    
    min_sem = defaut 0.3 Poss de passer un vecteur
    #delta_thetas = changement minimum dans le théta
    #thetas.start = vecteur de départ
    #min_items
    #max_items
    #theta_range: Upper and lower range for the theta integration grid. Used in conjunction with quadpts to generate an equally spaced quadrature grid. Default is c(-6,6)
    #content Type de contenu mesuré
    #content_prop proportion de chaque type de contenu
    #exposure Doit avoir la longeur du nombre d'items, nombre de phrases à considérer pour chaque point. Poss de donner une proba, qui permet de déterminer aléatoirement si l'item est donné
    #constraints: not_scored, excluded, independent, ordered"""

    design = robjects.r('list(min_items = {}, max_items={})'.format(
        current_app.config["NB_QUEST_MIN"], current_app.config["NB_QUEST_MAX"]))

    # print(mirt_object)
    pattern = mirtCAT.generate_pattern(
        mirt_object, Theta=pd.Series([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))

    mirtcat_obj = mirtCAT.mirtCAT(mo=mirt_object,
                                  method="ML",
                                  criteria="DPrule",  # 'MI' for the maximum information, 'MEPV' for minimum expected posterior variance, 'MLWI' for maximum likelihood weighted information, 'MPWI' for maximum posterior weighted information, 'MEI' for maximum expected information, and 'IKLP' as well as 'IKL' for the integration based Kullback-Leibler criteria with and without the prior density weight, respectively, and their root-n items administered weighted counter-parts, 'IKLn' and 'IKLPn'
                                  start_item="DPrule",
                                  design_elements=True,
                                  cl=cl,  # Cluster
                                  primeCluster=True,
                                  # progress=True, #Affiche une barre de progrès sur la console
                                  local_pattern=pattern,
                                  design=design,
                                  SE=1.96)  # SE: Intervallle de confiance à 95%

    return mirtcat_obj

# Dans reponses, passer correct/incorrect


def mirtcat_next_item(mirtcat_obj, questions_repondues=list(), reponses=None):

    # Renvoie l'iD de la prochaine question, et met à jour les thétas

    # print(mirtcat_obj)
    _mirtcat_obj = mirtcat_obj[2]
    upd = _mirtcat_obj.slots['Update.thetas']

    if reponses:
        mirtCAT.updateDesign(mirtcat_obj, items=robjects.r('c({})'.format(",".join(
            [str(x) for x in questions_repondues]))), responses=pd.Series(reponses))

        upd(mirtcat_obj[2], mirtcat_obj[0], mirtcat_obj[1])

    next_item = mirtCAT.findNextItem(mirtcat_obj)[0]

    return next_item


# Ajouter un critère d'arrêt en fonction des SE des thétas. On peut aussi imaginer un cas où quand une catégorie a atteinnt un SE suffisamment bas, on l'écarte.
def next_question(questions=[], reponses=None):

    # Vérification de l'état du test: si la cible est atteinte, on arrête
    if len(questions) >= 50:
        #print("Condition de longueur atteinte")
        return None

    # Sélection aléatoire
    if random() < 0.6:
        print("Aléatoire")
        return db.session.query(Phrase.id_phrase).join(StatsPhrases).filter(StatsPhrases.nb_reponses < 20).filter(Phrase.statut == "En évaluation").order_by(func.random()).first()

    # Sélection via mirtCAT
    else:
        print("Mirtcat")
        return mirtcat_next_item(generer_objet_mirtcat(mirt_obj_from_db()), questions_repondues=questions, reponses=reponses)


def mirt_obj_from_db():

    # Matrice difficultes
    # Extraction des id_difficulte pour chaque phrase
    phr_diff = db.session.query(
        Phrase.difficulte_id, StatsPhrases.phrase_id).join(StatsPhrases).all()
    # Classement dans l'ordre des questions
    phr_diff = sorted(phr_diff, key=lambda x: x[1])

    cov = sorted(list(set(x[0] for x in phr_diff)))

    mx = []

    # a
    for diff in sorted(list(set(x[0] for x in phr_diff))):
        mx.append([db.session.query(StatsPhrases.irt_a1).filter(StatsPhrases.phrase_id == x[1]).first()[0]
                   if x[0] == diff else 0 for x in phr_diff])

    # d
    mx.append([db.session.query(StatsPhrases.irt_d).filter(StatsPhrases.phrase_id == x[1]).first()[0]
               for x in phr_diff])
    # g
    mx.append([db.session.query(StatsPhrases.irt_g).filter(StatsPhrases.phrase_id == x[1]).first()[0]
               for x in phr_diff])
    # u
    mx.append([db.session.query(StatsPhrases.irt_u).filter(StatsPhrases.phrase_id == x[1]).first()[0]
               for x in phr_diff])

    # Passage sous Pandas et rotation
    df = pd.DataFrame(mx).transpose()

    # Ajout des titres de colonnes
    a = ["a" + str(x)
         for x in range(1, len((set(x[0] for x in phr_diff))) + 1)]
    a.extend(["d", "g", "u"])
    df.columns = a

    # Passage sous R
    #df_diffs_r = pandas2ri.py2ri(df)

    # Means
    means = [db.session.query(StatsDifficultes.irt_mean).filter(StatsDifficultes.difficulte_id == x).first()[0]
             for x in cov]

    # Covariance Matrix
    mx_cov = []

    lg = len(cov)
    for x in cov:
        row = []
        for y in cov:
            _r = db.session.query(CovMatrix.valeur).filter(
                CovMatrix.diff_row == str(x)).filter(CovMatrix.diff_col == str(y)).first()[0]
            row.append(_r)
        mx_cov.append(row)

    mx_cov = pd.DataFrame(mx_cov).values

    return mirtCAT.generate_mirt_object(df, "2PL", latent_means=means, latent_covariance=mx_cov)


def get_thetas(questions_repondues=list(), reponses=None):

    mirtcat_obj = generer_objet_mirtcat(mirt_obj_from_db())
    # print(mirtcat_obj)
    _mirtcat_obj = mirtcat_obj[2]
    upd = _mirtcat_obj.slots['Update.thetas']

    if reponses:
        mirtCAT.updateDesign(mirtcat_obj, items=robjects.r('c({})'.format(",".join(
            [str(x) for x in questions_repondues]))), responses=pd.Series(reponses))

        upd(mirtcat_obj[2], mirtcat_obj[0], mirtcat_obj[1])

    _m = mirtcat_obj[0]

    return list(_m.slots['.xData']['thetas'])


# def chargement_mirt_obj_vers_redis(mirt_obj):
