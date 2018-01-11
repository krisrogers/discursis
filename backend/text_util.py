"""Text utility functions."""
import os
import re

import jieba


# Match all word contractions, except possessives which we split to retain the root owner.
# We discard possessives because the are of no use (in english anyway).
# TODO: This won't work for languages like French!!
RE_CONTRACTION = "([A-Za-z]+\'[A-RT-Za-rt-z]+)"

# Email pattern, lifted from http://www.regular-expressions.info/email.html
RE_EMAIL = "(\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}\\b)"

# Capture decimal numbers with allowable punctuation that would get split up with the word pattern
RE_NUM = u"(\d+(?:[\.\,]{1}\d+)+)"

# Basic word pattern, strips all punctuation besides special leading characters
RE_WORD = u"([#@]?\w+)"

# URL pattern (Based on http://stackoverflow.com/questions/833469/regular-expression-for-url)
RE_URL = u"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[\-;:&=\+\$,\w]+@)?[A-Za-z0-9\.\-]+|(?:www\.|[\-;:&=\+\$,\w]+@)[A-Za-z0-9\.\-]+)((?:\/[\+~%\/\.\w\-_]*)?\??(?:[\-\+=&;%@\.\w_]*)#?(?:[\.\!\/\\\w]*))?)"

RE_TERM = re.compile(RE_URL + '|' + RE_EMAIL + '|' + RE_NUM + '|' + RE_CONTRACTION + '|' + RE_WORD, re.UNICODE)


# Load stopwords
STOPWORDS = None
with open(os.path.join(os.path.dirname(__file__), 'resources', 'stopwords-english.txt')) as stopwords_file:
    STOPWORDS = set([line.strip() for line in stopwords_file])


def tokenize(text, language='english', lowercase=True, min_word_length=0, stopwords=None):
    """
    Iteratively yield tokens as strings, optionally also lowercasing them and/or filtering by `min_word_length`.

    The tokens on output are maximal contiguous sequences of alphabetic characters.
    """
    language = language.lower()
    print(language)
    if language == 'english':
        stopwords = stopwords or STOPWORDS
        if lowercase:
            text = text.lower()
        for match in RE_TERM.finditer(text):
            word = match.group()
            if len(word) >= min_word_length and word not in stopwords:
                yield word
    elif language == 'chinese':
        for word in jieba.cut(text):
            if RE_TERM.match(word):
                yield word
    else:
        raise ValueError('Unsupported language {}'.format(language))
