import gensim
from nltk.tokenize import sent_tokenize, word_tokenize
import logging
import os
import sys

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class MySentences(object):
    def __init__(self, dirname):
       self.dirname = dirname
    def __iter__(self):
        for fname in os.listdir(self.dirname):
            for line in open(os.path.join(self.dirname, fname)):
                yield line.split()
def read_input(input_folder):
    text = ''
    for file in os.listdir("./" + input_folder):
        if file.endswith(".txt"):
            with open(os.path.join("./" + input_folder + '/',  file)) as f:
                text += f.read()
    print(text)
    return sent_tokenize(text)


if __name__ == '__main__':
    sentences = MySentences('./algo_training/') # a memory-friendly iterator
    model = gensim.models.Word2Vec(sentences, min_count=10, workers=4)
    model.save('word2vec100.model')
