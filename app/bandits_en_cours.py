#!encoding: utf-8
#!python 3


from flask_mab.storage import JSONBanditStorage
from flask_mab.bandits import EpsilonGreedyBandit

#Frequence de l'affichage
image_score_bandit_freq = EpsilonGreedyBandit(epsilon=0.95)
image_score_bandit_freq.add_arm("pas d'image",0)
#image_score_bandit_freq.add_arm("5q", 5)
image_score_bandit_freq.add_arm("10q", 10)
image_score_bandit_freq.add_arm("20q",20)


#Durée de l'affichage
image_score_bandit_duree = EpsilonGreedyBandit(epsilon=0.95)
image_score_bandit_duree.add_arm("1s",1)
image_score_bandit_duree.add_arm("3s",3)
image_score_bandit_duree.add_arm("5s",5)
