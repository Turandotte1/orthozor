import gensim
import matplotlib.pyplot as plt
import math
from sklearn.manifold import TSNE
import numpy as np
import matplotlib.pyplot as plt
from closest_words import closestwords_tsnescatterplot
import sys
import os

def draw_plt():
    word_presents = ''
    word_labels = []
    list = []
    dir = os.path.dirname(os.path.abspath(__file__))

    model = gensim.models.Word2Vec.load(dir + '/word2vec100.model')

    for words in model.wv.vocab :
        wrd_vector = model.wv[words]
        word_labels.append(words)
        list.append(wrd_vector)
    arr = np.array(list)
    tsne = TSNE(n_components=2, random_state=0, early_exaggeration=10000, learning_rate=500)
    np.set_printoptions(suppress=True)
    Y = tsne.fit_transform(arr)
    x_coords = Y[:, 0]
    y_coords = Y[:, 1]
    plt.scatter(x_coords, y_coords)

    plt.xlim(x_coords.min() - 25.00005, x_coords.max() + 25.00005)
    plt.ylim(y_coords.min() - 25.00005, y_coords.max() + 25.00005)
    plt.scatter(0, 0)
    plt.title('Victor', fontsize=18)
    plt.savefig('figure.png')


if __name__ == '__main__':
        draw_plt()
