import copy
import os
import json
import argparse
from collections import defaultdict
import re


def parse_words_from_data_file(dfile):
    """
    Data File Format
    synset_offset
    lex_filenum
    ss_type := n=NOUN v=VERB a=ADJECTIVE s=ADJECTIVE SATELLITE r=ADVERB
    w_cnt := two-digit hexadecimal integer
    [word  lex_id] + := ASCII form of a word … with spaces replaced by _
    [ptr] +
    [frames] +
    | gloss
    """
    words = defaultdict(lambda: {"word": None, "syns": set()})
    for line in dfile:
        if line[0] == " ":
            continue
        descriptior, _, gloss = line.partition(" | ")
        dparts = descriptior.strip().split(" ")
        wcnt = int(dparts[3], 16)
        line_words = set()
        for i in range(wcnt):
            word = dparts[4 + 2 * i]
            word = word.replace("_", " ")
            word = re.sub(r"\(.*\)$", "", word)
            line_words.add(word)
        for word in line_words:
            words[word]["word"] = word
            other_words = line_words - {word}
            words[word]["syns"] = list(other_words)
    return words.values()


def parse_wordnet_to_json(args):

    wn_data = defaultdict(
        lambda: {
            "word": None,
            "morph": "",
            "syns": [],
            "offensive": None,
            "topo": None,
            "nomen": None,
        }
    )

    for lex in ["noun", "verb", "adj", "adv"]:
        morph = lex[0].upper()
        data_filename = os.path.join(args.wordnet_base, f"data.{lex}")
        # index_filename = os.path.join(args.wordnet_base, f"index.{lex}")
        print(f"Parsing {lex} data...")
        with open(data_filename, "r") as data_file:
            wn_lex_data = parse_words_from_data_file(data_file)
        for word_data in wn_lex_data:
            word = word_data["word"]
            if not word or word[0].isdigit() or not word[0].isalpha():
                print(f"... skipping `{word}`")
                continue
            if " " in word:
                print(f"... skipping `{word}`")
                continue
            wn_data[word]["word"] = word_data["word"]
            if wn_data[word]["syns"] and word_data["syns"]:
                wn_data[word]["syns"] += word_data["syns"]
            else:
                wn_data[word]["syns"] = word_data["syns"]
            if morph not in wn_data[word]["morph"]:
                wn_data[word]["morph"] += morph
            if word[0].isupper():
                wn_data[word]["topo"] = True
        print(f"+{len(wn_lex_data)=} ={len(wn_data)=}")

    wn_data = [copy.copy(v) for v in wn_data.values()]
    wn_data.sort(key=lambda x: x["word"])

    with open(args.output, "w") as json_file:
        json.dump(wn_data, json_file, indent=2, sort_keys=True, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Parse WordNet data to JSON format.")
    parser.add_argument("wordnet_base", type=str)
    parser.add_argument("output", type=str)
    args = parser.parse_args()

    parse_wordnet_to_json(args)


if __name__ == "__main__":
    main()
