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
    r"===\s*Морфологические и синтаксические свойства\s*===(.*?)(===|$)",
    re.I | re.DOTALL,
)
ANTONYMS_RE = re.compile(
    r"====\s*Антонимы\s*====(.*?)(====|$)",
    re.I | re.DOTALL,
)
SYNONYMS_RE = re.compile(
    r"====\s*Синонимы\s*====(.*?)(====|$)",
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
                self.output.append(data)
                if len(data["morph"]) > 1 or len(self.output) % 100 == 0:
                    print(f"{len(self.output)}/{self.pages}, {data}", file=sys.stderr)
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

    PAGE_LANG_BLOCK_SPLIT_RE = re.compile(r"= {{-([a-z]+)-}} =", re.I | re.DOTALL)

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

        # True or None (certain or uncertain, because not detected)
        offensive = (text.find("""{{offensive}}""") >= 0) or None

        # === Морфо
        morph, topo, nomen = "", None, None

        for mo in MORPH_RE.finditer(text):
            txt_morph = mo.group(1)
            if (
                txt_morph.find("\n{{сущ " + self.lang) >= 0
                or txt_morph.find("\n{{сущ-" + self.lang) >= 0
            ):
                morph += "N"
            if txt_morph.find("\n{{гл " + self.lang) >= 0:
                morph += "V"
            if txt_morph.find("\n{{прил " + self.lang) >= 0:
                morph += "A"
            if txt_morph.find("\n{{adv" + self.lang) >= 0:
                morph += "D"
            if txt_morph.find("\n{{числ " + self.lang) >= 0:
                morph += "9"
            if txt_morph.find("\n{{прич " + self.lang) >= 0:
                morph += "P"
            if txt_morph.find("\n{{мест " + self.lang) >= 0:
                morph += "Z"
            if txt_morph.find("\n{{abbrev") >= 0:
                morph += "B"

            topo = txt_morph.find("{{топоним") >= 0 or txt_morph.find("{{гидроним") >= 0
            nomen = (
                txt_morph.find("{{собств.") >= 0
                or "B" not in morph
                and title[0].isupper()
            )

        # неизвестная фигня
        if not morph:
            return None

        ants = []
        for mo in ANTONYMS_RE.finditer(text):
            # [[отмель]], [[мель]]; {{помета|частичн.}}, {{разг.|-}}: [[мелкота]]
            for w in wklinks_re.findall(mo.group(1)):
                ants.append(w)

        syns = []
        for mo in SYNONYMS_RE.finditer(text):
            # [[отмель]], [[мель]]; {{помета|частичн.}}, {{разг.|-}}: [[мелкота]]
            for w in wklinks_re.findall(mo.group(1)):
                syns.append(w)

        page = {
            "word": title,
            "syns": syns,
            "ants": ants,
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

        title = sstrip("".join(self.texts.get("title", [])))
        text = "".join(self.texts.get("text", []))

        if spsymbs_re.search(title):
            return None

        if text.find("""==English==""") < 0:
            return None

        enmo = self.ENGLISH_RE.search(text)
        if not enmo:
            return None

        text = enmo.group(1)

        # True or None (certain or uncertain, because not detected)
        offensive = (text.find("""{{offensive}}""") >= 0) or None

        morph = ""

        if re.search(r"^===Noun===\n{{en-noun", text, re.M | re.I):
            morph += "N"
        if re.search(r"^===Verb===\n{{en-verb", text, re.M | re.I):
            morph += "V"
        if re.search(r"^===Adjective===\n{{en-adj", text, re.M | re.I):
            morph += "A"
        if re.search(r"^===Adverb===\n{{en-", text, re.M | re.I):
            morph += "D"
        if re.search(r"^===Numeral===\n{{en-", text, re.M | re.I):
            morph += "9"
        if re.search(r"^===Pronoun===\n{{en-", text, re.M | re.I):
            morph += "P"
        if re.search(r"^===Proper noun===\n{{en-", text, re.M | re.I):
            morph += "Z"
        if re.search(r"^===Abbreviation===\n{{en-", text, re.M | re.I):
            morph += "B"

        topo = None  # FIXME
        nomen = None  # FIXME
        ants = []  # FIXME
        syns = []
        for mo in SYNONYMS_RE.finditer(text):
            # [[отмель]], [[мель]]; {{помета|частичн.}}, {{разг.|-}}: [[мелкота]]
            for w in wklinks_re.findall(mo.group(1)):
                syns.append(w)

        if morph:
            page = {
                "word": title,
                "syns": syns,
                "ants": ants,
                "morph": morph,
                "topo": topo,
                "nomen": nomen,
                "offensive": offensive,
            }
            return page


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
