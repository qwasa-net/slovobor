import re

import mysql_db as db
from settings import *

#
ABC_RUS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
ABC_ENG = "abcdefghijklmnopqrstuvwxyz"

if LANG == 1:
    ABC_STR = ABC_RUS
elif LANG == 2:
    ABC_STR = ABC_ENG
elif LANG == 3:
    ABC_STR = ABC_RUS + ABC_ENG

ABC = list(ABC_STR)
NOABC_RE = re.compile('[^%s]' % (ABC_STR))


def count_abc(word, abc=None):
    return [word.count(l) for l in abc or ABC]


def clean_word(word):
    return NOABC_RE.sub('', (word or "").lower())


def get_words(word=None, abcs=None, only_nouns=True, skip_offensive=True,
              min_length=MIN_LENGTH, max_results=MAX_RESULTS, lang=LANG):

    if not word:
        return None, 0

    lc = []  # count letters in the `word`
    for l in ABC:
        lc.append("%i, " % (word.count(l)))

    # compile DB query
    query = """CALL GET_WORDS(%s %i, %i, %i, %i, %i)""" % (
        "".join(lc),
        min_length,
        max_results,
        lang,
        1 if only_nouns else 0,
        1 if skip_offensive else 0
    )

    cnx = db.connect(DB_USER, DB_PASS, DB_NAME, host=DB_HOST, unix_socket=DB_UNIX)
    rc, results = db.execute(cnx, query)
    db.close(cnx)

    if rc and results and len(results) > 0:
        return results[0]

    return None, 0
