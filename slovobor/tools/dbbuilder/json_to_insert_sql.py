import json
import sys
import re

import logging
logger = logging.getLogger(__name__)

#
LANG = 1
ABCLIMIT = 33
ABC = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz")[:ABCLIMIT]

INSERT_MAX = 10000


def count_abc(word, abc=None):
    return [word.count(i) for i in (abc or ABC)]


if __name__ == "__main__":

    if len(sys.argv) > 1:
        infile_name = sys.argv[1]
        infile = open(infile_name)
    else:
        infile_name = None
        infile = sys.stdin

    data = json.load(infile)

    word_types = {"N": 1, "V": 2, "A": 3, '9': 4, 'B': 5, 'D': 6, 'P': 7, 'Z': 8}

    insert_words = []
    insert_words.append("""SET names utf8;\n""")  # MySQL

    insert_words_letters = []
    insert_words_letters.append("""SET names utf8;\n""")  # MySQL

    i, c, ic = 0, 0, 0
    word_types_stats = {}
    ls_labels = ", ".join(["l%s" % i for i in range(1, 1 + len(ABC))])
    for word in data:

        if i % INSERT_MAX == 0:
            if i > 0:
                insert_words.append(";\n")
                insert_words_letters.append(";\n")
                ic = 0
            insert_words.append(
                ("""INSERT INTO words """
                 """(id, word, first, last, last2, length, lang, morph, topo, nomen, offensive, %s) """
                 """VALUES \n""") % (ls_labels)
            )

        i += 1

        # INSERT INTO words (id, word, first, last, last2, length, lang, type, topo, nomen, l1 … lN) VALUES (…)
        w = word['word']
        l = len(w)
        w0 = word['word'].lower()
        if l < 2 or l > 40:
            logger.warning("word skipped: #%s `%s` %s", i, w, l)
            continue

        c += 1
        ic += 1
        morph = word_types.get(word['morph'], "NULL")
        word_types_stats[morph] = word_types_stats.get(morph, 0) + 1

        # INSERT INTO words_letters (word_id, l1 … l99) VALUES (…)
        w0 = word['word'].lower().replace('-', '')
        counts = count_abc(w0)
        if sum(counts) != len(w0):
            logger.warning("sum(count_abc) != len(word) %s (%s) => %s", w0, list(word.values()), "|".join(map(str, counts)))
            logger.warning("word skipped: #%s `%s` %s", i, w, l)

        ls_counts = ",".join(map(str, counts))
        sql_format = """(%s, "%s", "%s", "%s", "%s", %s, %s, %s, %s, %s, %s, %s)"""
        # """(id, word, first, last, last2, length, lang, morph, topo, nomen, offensive, %s) """
        sql = sql_format % (
            i, w, w[0], w[-1], w[-2], l, LANG, morph,
            1 if word['topo'] else 0,
            1 if word['nomen'] else 0,
            1 if word['offensive'] else 0,
            ls_counts
        )
        if ic > 1:
            insert_words.append(",\n")
        insert_words.append(sql)

    insert_words.append(";")

    if infile_name is None:
        outfile_name = None
        outfile = sys.stdout
    else:
        outfile_name = infile_name.replace('.json', '.sql')
        outfile = open(outfile_name, 'w')

    outfile.write("".join(insert_words))

    logger.warning("stats i=%s c=%s, %s", i, c, word_types_stats)
    logger.warning("outfile = %s", outfile_name)
