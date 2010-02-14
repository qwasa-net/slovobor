import json
import re
import sys
import xml.sax
import argparse

whends_re = re.compile(r'(^[\s\n\r]+|[\s\n\r]+$)', re.I | re.U | re.M)
whends0_re = re.compile(r'(^[\s\n\r]+)|([\s\n\r]+$)', re.I | re.U)
whites_re = re.compile(r'[\s\n\r]+', re.I | re.U | re.M)
whites0_re = re.compile(r'[ ]{2,}', re.I | re.U | re.M)

wiki_cleanup_magic_words = re.compile(r'__([A-Z]{3,})__', re.U | re.M)


def sstrip(t):

    if not t:
        return ""
    t = whends_re.sub('', t)
    t = whites_re.sub(' ', t)
    return t


def int0(s):
    try:
        return int(s)
    except Exception:
        return 0


spsymbs_re = re.compile(r'[:/\[\]\s]')

wklinks_re = re.compile(r'\[\[([a-zA-Zа-яА-Я]{4,})\]\]')
morph_re = re.compile(r'===\s*Морфологические и синтаксические свойства\s*===(.*?)===', re.I | re.DOTALL)
ant0_re = re.compile(r'====\s*Антонимы\s*====(.*?)====', re.I | re.DOTALL)
sin0_re = re.compile(r'====\s*Синонимы\s*====(.*?)====', re.I | re.DOTALL)


class WikiReader(xml.sax.handler.ContentHandler):

    def __init__(self, **kwargs):
        self.mode = None
        self.level = 0
        self.levels = []
        self.pages = 0
        self.texts = {}

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
                output.append(data)
                if len(output) % 1000 == 0:
                    print(self.pages, len(output), data['word'], file=sys.stderr)
            self.texts = {}

        elif self.levels:
            self.levels.pop()

    def characters(self, content):
        if self.levels:
            name = self.levels[-1]
            if name not in self.texts:
                self.texts[name] = [content, ]
            else:
                self.texts[name].append(content)

    def process_page(self):

        title = sstrip("".join(self.texts.get('title', [])))
        text = "".join(self.texts.get('text', []))

        if spsymbs_re.search(title):
            return None

        if text.find("""{{-ru-}}""") < 0:
            return None

        # True or None (certain or uncertain, because not detected)
        offensive = (text.find("""{{offensive}}""") >= 0) or None

        # === Морфо
        morph, topo, nomen = None, None, None
        mo = morph_re.search(text)
        if mo:
            tmo = mo.group(1)
            if tmo.find('{{сущ') >= 0:
                morph = "N"
            elif tmo.find('{{гл') >= 0:
                morph = 'V'
            elif tmo.find('{{прил') >= 0:
                morph = 'A'
            elif tmo.find('{{adv') >= 0:
                morph = 'D'
            elif tmo.find('{{числ') >= 0:
                morph = '9'
            elif tmo.find('{{прич') >= 0:
                morph = 'P'
            elif tmo.find('{{мест') >= 0:
                morph = 'Z'
            elif tmo.find('{{abbrev') >= 0:
                morph = 'B'

            topo = tmo.find('{{топоним') >= 0 or tmo.find('{{гидроним') >= 0
            nomen = tmo.find('{{собств.') >= 0 or (morph != 'B' and title[0].isupper())

        ants = []
        mo = ant0_re.search(text)
        if mo:
            # [[отмель]], [[мель]]; {{помета|частичн.}}, {{разг.|-}}: [[мелкота]]
            for w in wklinks_re.findall(mo.group(1)):
                ants.append(w)

        syns = []
        mo = sin0_re.search(text)
        if mo:
            # [[отмель]], [[мель]]; {{помета|частичн.}}, {{разг.|-}}: [[мелкота]]
            for w in wklinks_re.findall(mo.group(1)):
                syns.append(w)

        if morph is not None:
            return {'word': title,
                    'syns': syns,
                    'ants': ants,
                    'morph': morph,
                    'topo': topo,
                    'nomen': nomen,
                    'offensive': offensive}

output = []


def save_output(fn="data.json"):
    f = open(fn, 'w')
    f.write(json.dumps(output, indent=0, ensure_ascii=False))
    f.close()


if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] != "-":
        infile = open(sys.argv[1])
    else:
        infile = sys.stdin

    if len(sys.argv) > 2:
        outfile = sys.argv[2]
    else:
        outfile = "data-done.json"

    print("wiki → json: (%s)→(%s)" % (infile, outfile), file=sys.stderr)

    wiki = WikiReader()
    parser = xml.sax.make_parser()
    parser.setContentHandler(wiki)
    parser.parse(infile)
    save_output(outfile)
