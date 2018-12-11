from nltk.tokenize import sent_tokenize, word_tokenize
import re
import sys
import copy

def check_words(filename):
    with open(filename) as f:
        text = f.read()
    sentences = sent_tokenize(text)
    for sentence in sentences:
        if (len(word_tokenize(sentence)) > 3):
            print(sentence.replace('\n', ''))

if __name__ == '__main__':
        check_words(sys.argv[1])
