import bz2
import json
import re
import sys
import xml.sax
import argparse

whends_re = re.compile(r"(^[\s\n\r]+|[\s\n\r]+$)", re.I | re.U | re.M)
whends0_re = re.compile(r"(^[\s\n\r]+)|([\s\n\r]+$)", re.I | re.U)
whites_re = re.compile(r"[\s\n\r]+", re.I | re.U | re.M)
whites0_re = re.compile(r"[ ]{2,}", re.I | re.U | re.M)

wiki_cleanup_magic_words = re.compile(r"__([A-Z]{3,})__", re.U | re.M)


def sstrip(t):

    if not t:
        return ""
    t = whends_re.sub("", t)
    t = whites_re.sub(" ", t)
    return t


def int0(s):
    try:
        return int(s)
    except Exception:
        return 0


spsymbs_re = re.compile(r"[:/\[\]\s]")

wklinks_re = re.compile(r"\[\[([a-zA-Zа-яА-Я]{4,})\]\]")

MORPH_RE = re.compile(
    r"===\s*Морфологические и синтаксические свойства\s*===(.*?)(\n=|$)",
    re.I | re.DOTALL,
)
ANTONYMS_RE = re.compile(
    r"====\s*Антонимы\s*====[\s\n\r]+(.*?)(\n=|$)",
    re.I | re.DOTALL,
)
SYNONYMS_RE = re.compile(
    r"====\s*Синонимы\s*====[\s\n\r]+(.*?)(\n=|$)",
    re.I | re.DOTALL,
)
MEANING_RE = re.compile(
    r"====\s*Значение\s*====[\s\n\r]+(.*?)(\n=|$)",
    re.I | re.DOTALL,
)


class WikiReader(xml.sax.handler.ContentHandler):

    def __init__(self, **kwargs):
        self.mode = None
        self.level = 0
        self.levels = []
        self.pages = 0
        self.texts = {}
        self.output = []
        self.lang = kwargs.get("lang", "ru")
        self.uniques = set()

    def startElement(self, name, attrs):
        self.level += 1
        self.levels.append(name)

    def endElement(self, name):
        self.level -= 1

        if name == "page":
            self.mode = None
            self.levels = []
            self.pages += 1
            data = self.process_page()
            if data:
                if data["word"] in self.uniques:
                    print(f"#! DUP: {data['word']}", file=sys.stderr)
                self.uniques.add(data["word"])
                # if data["offensive"]:
                #     print(f"!OFF: {data['word']} {data['syns']}", file=sys.stderr)
                if len(self.output) % 1000 == 1:
                    print(f"#~ {len(self.output)}/{self.pages}: {data}", file=sys.stderr)
                self.output.append(data)
            self.texts = {}

        elif self.levels:
            self.levels.pop()

    def characters(self, content):
        if self.levels:
            name = self.levels[-1]
            if name not in self.texts:
                self.texts[name] = [content]
            else:
                self.texts[name].append(content)

    def process_page(self):
        return None


class RUWikiReader(WikiReader):
    """ """

    # {{-ru-}} -- начало блока для языка
    PAGE_LANG_BLOCK_SPLIT_RE = re.compile(r"^=\s+{{-([a-z]+)-}}\s+=$", re.I | re.M)

    def get_lang_block(self, text, lang):
        start, end = 0, len(text)
        while True:
            mo = self.PAGE_LANG_BLOCK_SPLIT_RE.search(text, start)
            if not mo:
                return None
            start = mo.end(0)
            if mo.group(1) == lang:
                break
        mo = self.PAGE_LANG_BLOCK_SPLIT_RE.search(text, start)
        if mo:
            end = mo.start(0)
        return text[start:end]

    def process_page(self):

        title = sstrip("".join(self.texts.get("title", [])))
        text = "".join(self.texts.get("text", []))

        if spsymbs_re.search(title):
            return None

        text = self.get_lang_block(text, self.lang)
        if not text:
            return None

        # === Морфо
        morph, topo, nomen = "", None, None

        for mo in MORPH_RE.finditer(text):  # слово одно -- смыслов несколько
            mrph_txt = mo.group(1)
            if (
                re.search(r"\n{{\s*сущ[\- ]+" + self.lang, mrph_txt, re.I | re.M)
                or re.search(r"\n{{\s*падежи\s*\n", mrph_txt, re.I | re.M)
                or False
            ):
                morph += "N"
            if re.search(r"\n{{\s*гл[\- ]+" + self.lang, mrph_txt, re.I | re.M):
                morph += "V"
            if (
                re.search(r"\n{{\s*прил[\- ]+" + self.lang, mrph_txt, re.I | re.M)
                or re.search(r"\n{{\s*Мс-п6", mrph_txt, re.I | re.M)
                or False
            ):
                morph += "A"
            if re.search(r"\n{{\s*числ[\- ]+", mrph_txt, re.I | re.M):
                morph += "9"
            if re.search(r"\n{{\s*adv[\- ]+" + self.lang, mrph_txt, re.I | re.M):
                morph += "D"
            if re.search(
                r"\n{{\s*(adv|predic|conj)[\- ]+" + self.lang, mrph_txt, re.I | re.M
            ):
                morph += "R"
            if re.search(r"\n{{\s*(прич|деепр)[\- ]+", mrph_txt, re.I | re.M):
                morph += "P"
            if re.search(r"\n{{\s*мест[\- ]+", mrph_txt, re.I | re.M):
                morph += "Z"
            if re.search(r"\n{{\s*prep[\- ]+", mrph_txt, re.I | re.M):
                morph += "S"
            if re.search(r"\n{{\s*(intro|part)[\- ]+", mrph_txt, re.I | re.M):
                morph += "T"
            if re.search(r"\n{{\s*abbrev", mrph_txt, re.I | re.M):
                morph += "B"
            if re.search(r"\n{{\s*Фам[\- ]+", mrph_txt, re.M):
                morph += "F"
            if re.search(r"\n{{\s*interj[\- ]+", mrph_txt, re.I | re.M):
                morph += "J"
            if re.search(r"\n{{\s*onomatop[\- ]+", mrph_txt, re.I | re.M):
                morph += "O"
            topo = mrph_txt.find("{{топоним") >= 0 or mrph_txt.find("{{гидроним") >= 0
            nomen = (
                mrph_txt.find("{{собств.") >= 0
                or "B" not in morph
                and title[0].isupper()
            )

        # неизвестная фигня
        if not morph or morph == "F":
            if (
                not morph
                and len(title) > 2
                and not title[0].isupper()
                and "-" not in title
                and "." not in title
            ):
                print(f"#! MORPH: {title} {self.lang}", file=sys.stderr)
            return None

        offensive = None
        mean_mo = MEANING_RE.search(text)
        if mean_mo:
            mean_text = mean_mo.group(1)
            mean_first = mean_text.split("\n")[0]
            if mean_first.find("{{обсц.") >= 0 or mean_first.find("{{вульг.") >= 0:
                # print(f"#MEAN: {mean_first}", file=sys.stderr)
                offensive = True

        ants = set()
        for mo in ANTONYMS_RE.finditer(text):  # антонимы к каждому смыслу
            for w in wklinks_re.findall(mo.group(1)):
                ants.add(w)

        syns = set()
        for mo in SYNONYMS_RE.finditer(text):  # синонимы к каждому смыслу
            for w in wklinks_re.findall(mo.group(1)):
                syns.add(w)

        page = {
            "word": title,
            "syns": list(syns),
            "ants": list(ants),
            "morph": "".join(sorted(set(morph))),
            "topo": topo,
            "nomen": nomen,
            "offensive": offensive,
        }
        return page


class ENWikiReader(WikiReader):

    ENGLISH_RE = re.compile(
        r"==English==(.+?)(===[a-z]+===|$)",
        re.M | re.I | re.DOTALL,
    )

    def __init__(self, **kwargs):
        raise NotImplementedError("ENWikiReader is not implemented yet")
        super().__init__(**kwargs)

    def process_page(self):
        return {}


def save_output(fn="data.json", output=None):
    f = open(fn, "w")
    f.write(json.dumps(output, indent=0, ensure_ascii=False))
    f.close()


def main():

    parser = argparse.ArgumentParser(description="Parse RUWiktionary XML dump to JSON.")
    parser.add_argument("input", default="-", nargs="?")
    parser.add_argument("output", default="data-done.json", nargs="?")
    parser.add_argument("--lang", default="ru")
    args = parser.parse_args()

    infile_name = args.input
    if infile_name == "-" or not infile_name:
        infile = sys.stdin
    else:
        if infile_name.endswith(".bz2"):
            infile = bz2.BZ2File(infile_name)
        else:
            infile = open(infile_name)

    outfile_name = args.output
    print("wiki → json: (%s)→(%s)" % (infile, outfile_name), file=sys.stderr)

    wiki = RUWikiReader(lang=args.lang)
    parser = xml.sax.make_parser()
    parser.setContentHandler(wiki)
    parser.parse(infile)
    save_output(outfile_name, wiki.output)


if __name__ == "__main__":
    main()
