import bz2
import argparse
import itertools
import json
import struct
import sys
from collections import Counter, defaultdict
from statistics import mean, median

from icu import LocaleData


def fillit(size=0, fill=b"\x00"):
    return (fill * size)[:size]


FORMAT_SIZE = {1: "B", 2: "H", 4: "I"}


class SlvbrDB:

    # DB := MAGIC (8b) META (+b) RECORDS (+b) BOG (+b) TOC (+b)

    def __init__(self, title, encoding, lines):
        self.magic = Magic()
        self.bog = Bog(lines)
        self.toc = TOC(lines)
        self.tags = TagsDict(lines)
        self.meta = Meta(title, encoding, lines, self.bog, self.toc)
        self.lines = lines

    def data(self):
        binary = self.magic.data()
        binary += self.meta.data()
        for line in self.lines:
            binary += line.data()
        return binary

    def goto(self, out, to, fill=b"\x00"):
        pos = out.tell()
        size = to - pos
        out.write(fillit(size, fill))

    def write(self, out):
        """…"""

        print(f"[X] ...         ={out.tell()}")

        print(f"[1] magic       ={out.tell()}")
        out.write(self.magic.data())

        print(f"[2] meta        ={out.tell()}")
        out.write(self.meta.data())

        print(f"[2] tags        ={out.tell()}")
        out.write(self.tags.data())

        self.goto(out, 1024, b"\xee")
        print(f"[3] lines     ={out.tell()}")
        for i, line in enumerate(self.lines):
            if i < 3 or i % 20000 == 0:
                print(f"[3.{i}] {line} ={out.tell()}")
            line.write(out)

        print(f"[4] bog         ={out.tell()}")
        self.bog.write(out)

        print(f"[5] toc         ={out.tell()}")
        self.toc.write(out)

        print(f"[X] ...         ={out.tell()} {out.tell() / (1024**2):.1f}MB")


class Magic:

    # MAGIC := "!slvBR" (6b) + VERSION (int16, 2b)
    # VERSION := 0x0001

    MAGIC = b"!slvBR"
    VERSION = 0x0001
    TEMPLATE = "<6sH"
    LEN = 8

    def data(self):
        return struct.pack(Magic.TEMPLATE, Magic.MAGIC, Magic.VERSION)


class Meta:

    # META := META_LEN (int32, 4b) + META_DATA (META_LEN bytes)
    # META_DATA :=
    #   TITLE (128b)
    #   ENCODING (8b)
    #   RECORDS_COUNT (4b)
    #   RECORD_LEN (4b)
    #   TAGS_COUNT (4b)
    #   TAG_LEN (4b) := 1
    #   TAG_TYPE_LEN (4b) := 1
    #   TAG_VALUE_LEN (4b) := 4
    #   BODY_LEN (4b) := 128
    #   TAG_DESCRIPTION (TAGS_COUNT × (TAG_TYPE_LEN + TAG_VALUE_LEN) b)

    TEMPLATE_DATA = "<128s8sIIIIIIIIIII"
    META_LEN = 1024

    def __init__(self, title, encoding, lines, bog, toc):
        self.title = title
        self.encoding = encoding
        self.lines = lines
        self.bog = bog
        self.toc = toc

    def data(self):
        r0 = self.lines[0]
        return struct.pack(
            Meta.TEMPLATE_DATA,
            self.title.encode("ascii", errors="ignore"),
            self.encoding.encode("ascii", errors="ignore"),
            self.META_LEN,
            len(self.lines),
            r0.length,
            r0.tags_count,
            r0.tag_len,
            TagsDict.TAG_TYPE_LEN,
            TagsDict.TAG_VALUE_LEN,
            r0.body_len,
            len(self.bog),
            self.toc.length,
            self.toc.count,
        )


class TagsDict:

    TAG_LEN = 1
    TAG_LEN_TEMPLATE = FORMAT_SIZE.get(TAG_LEN)

    TAG_TYPE_LEN = 2
    TAG_VALUE_LEN = 4

    def __init__(self, lines):
        self.lines = lines
        self.tags = lines[0].tags

    def data(self):
        binary = b""
        for tag in self.tags:
            binary += struct.pack(
                f"H{self.TAG_VALUE_LEN}s",
                tag[2],
                tag[0],
            )
        return binary


class Line:

    TAG_LEN = 1
    TAG_FORMAT = FORMAT_SIZE.get(TAG_LEN)

    BODY_LEN = 8
    BODY_TEMPLATE = "<II"

    def __str__(self):
        return f"Line({self.data_tags().hex()}, {self.bog_ptr})"

    def __repr__(self):
        return self.__str__()

    @property
    def length(self):
        return self.tags_count * self.tag_len + self.body_len

    @property
    def body_len(self):
        return self.BODY_LEN

    @property
    def body_offset(self):
        return self.tags_count * self.tag_len

    def __init__(self, tags, body):
        self.tags = tags
        self.tags_count = len(tags)
        self.tag_len = self.TAG_LEN  # v1
        self.tags_len = self.tags_count * self.tag_len
        self.body = body
        self.bog_ptr = (0, 0)

    def data_tags(self):
        binary = b"".join(
            (struct.pack(f"{Line.TAG_FORMAT}", tag[1]) for tag in self.tags)
        )
        return binary

    def data_bog_pointer(self):
        if self.bog_ptr is None:
            return b""
        return struct.pack(self.BODY_TEMPLATE, *self.bog_ptr)

    def write(self, out):
        bin_tags = self.data_tags()
        assert len(bin_tags) == self.tags_len, f"{len(bin_tags)=}"
        out.write(bin_tags)
        bin_bog_ptr = self.data_bog_pointer()
        assert len(bin_bog_ptr) == self.BODY_LEN, f"{len(bin_bog_ptr)=}"
        out.write(bin_bog_ptr)


class Bog:

    def __init__(self, lines):
        self.bog = bytes()
        self.lines = lines
        self.stats = [0, 0]
        print("bogging …")
        for line in reversed(lines):
            pointer = self.add(line.body)
            line.bog_ptr = (pointer, len(line.body))
        print(f"bogged {self.stats=} {len(self.bog)=}")

    def __len__(self):
        return len(self.bog)

    def add(self, bogus):
        found = self.bog.find(bogus)
        if found < 0:
            self.stats[0] += 1
            pos = len(self.bog)
            self.bog += bogus
            return pos
        else:
            self.stats[1] += 1
        return found

    def write(self, out):
        out.write(self.bog)


class TOC:

    TAG_LEN = 1
    TAG_FORMAT = FORMAT_SIZE.get(TAG_LEN)
    TOC_LEN = 4 + 4
    TOC_TEMPLATE = "<II"

    def __init__(self, lines, page_size=20):
        self.lines = lines
        self.page_size = page_size
        self.toc = []
        self.toq = []
        self.length = lines[0].tags_len + self.TOC_LEN
        self.build_toc()
        self.compresse_toc()

    @property
    def count(self):
        return len(self.toc)

    def build_toc(self):
        print("ToC'ing")
        toq = set()
        i = 0
        for rec_chunk in itertools.batched(self.lines, self.page_size):
            toc = [tag[1] for tag in rec_chunk[0].tags]
            c = 0
            for rec in rec_chunk:
                c += 1
                toc = min_line(toc, [tag[1] for tag in rec.tags])
            self.toc.append([toc, i, c])
            i += c
            toq.add(tuple(toc[:-4]))
        print(
            f"ToC'ed {len(self.toc)=} {len(toq)=} "
            f"{sum([x[2] for x in self.toc])=} "
            f"{max([x[2] for x in self.toc])=}"
        )

    def compresse_toc(self, cropper=-4):
        last = None
        for i, toc in enumerate(self.toc):
            if last is None:
                last = toc[0]
                continue
            if last[:cropper] == toc[0][:cropper]:
                self.toc[i][1] = self.toc[i - 1][1]
                self.toc[i][2] += self.toc[i - 1][2]
                self.toc[i - 1] = None
            else:
                last = toc[0]
        self.toc = list(filter(lambda x: x is not None, self.toc))
        toq = set([tuple(t[0][:cropper]) for t in self.toc])
        print(
            f"CToC'ed {len(self.toc)=} {len(toq)=} "
            f"{sum([x[2] for x in self.toc])=} "
            f"{max([x[2] for x in self.toc])=}"
        )

    def write(self, out):
        for i, toc in enumerate(self.toc):
            toc_tags = (
                struct.pack(
                    f"{self.TAG_FORMAT}",
                    tag,
                )
                for tag in toc[0]
            )
            binary = b"".join(toc_tags)
            binary += struct.pack(self.TOC_TEMPLATE, toc[1], toc[2])
            out.write(binary)


def main():
    args = parse_args()
    print(f"{args=}")

    # read words
    print("reading input …")
    words = read_input(args)

    # count letters
    print("counting letters …")
    words, letters = count_letters(words, args)
    max_word_len = max(map(lambda w: w["__len"], words))
    print(f"{len(words)=}, {len(letters)=}, {max_word_len=}")
    print(f"{words[1000]=}")

    # reorder tags
    print("reordering tags …")
    if args.best_tag_order:
        args.tags = reorder_tags(words, letters)
        print(f"{args.tags=}")

    # count ranking and sort for best tag
    print("counting ranking …")
    words = count_ranking(words, letters)
    words = sorted(words, key=lambda w: w["__ranking"], reverse=False)
    print(f"{words[1000]=}")
    show_boxes(words, args)

    # compile db
    print("compiling db …")
    db = compile_db(words, args)

    # save db
    print("saving db …")
    save_db(db, args)


def save_db(db, args):
    with open(args.output, "wb") as out:
        db.write(out)
        out.flush()


def compile_db(words, args):
    lines: list[Line] = []
    for i, word in enumerate(words):
        tags = [
            (
                c.encode(args.encoding, errors="ignore"),
                word["__counters"].get(c, 0),
                0,
            )
            for c in args.tags
        ]
        tags.append(
            (
                "~".encode(args.encoding, errors="ignore"),
                len(word["word"]),
                1,
            )
        )
        tags.append(
            (
                "~".encode(args.encoding, errors="ignore"),
                ord(word["morph"][0]),
                2,
            )
        )
        tags.append(
            (
                "~".encode(args.encoding, errors="ignore"),
                1 if word["topo"] else 2,
                3,
            )
        )
        tags.append(
            (
                "~".encode(args.encoding, errors="ignore"),
                1 if word["nomen"] else 2,
                3,
            )
        )
        body = word["word"].encode(args.encoding, errors="ignore")
        line = Line(tags, body)
        if i % 20000 == 2:
            print(f"compiling: {i=} {word['word']=} {line=}")
        lines.append(line)
    db = SlvbrDB("slovobor", args.encoding, lines)
    return db


def min_line(a, b):
    assert isinstance(a, list) and isinstance(b, list)
    assert len(a) == len(b)
    return [min(a[i], b[i]) for i in range(len(a))]


def show_boxes(words, args, index_size=8):
    current = None
    tagted = args.tags[:index_size]
    counters = []
    for word in words:
        word_index = [word["__counters"].get(c, 0) for c in tagted]
        if current is None:
            current = word_index
            counter = 1
        elif current != word_index:
            # print(f"{current=}, {counter=}, {word['word']=}")
            counters.append(counter)
            counter = 1
            current = word_index
        else:
            counter += 1
    print(f"{current=}, {counter=}, {word['word']=}")
    counters.append(counter)
    print(f"{median(counters)=}, {mean(counters)=}, {max(counters)=}, {len(counters)=}")


def reorder_tags(words, tags):

    cadidates = []
    for i in range(len(tags)):
        tag_splits = calculate_tag_splitting(words, cadidates)
        tag_splits = {
            k: v
            for (k, v) in sorted(
                filter(lambda x: x[0] not in cadidates, tag_splits.items()),
                key=lambda x: len(x[1]),
                reverse=True,
            )
        }
        # print(
        #     f"{'AZ':4s} | {'size':4s} {'total':8s} {'median':8s} {'mean':8s} | {'sizes':8s}"
        # )
        best = None
        totalled = 0
        if not tag_splits:
            break
        for letter, lc in tag_splits.items():
            # print(f"{letter:4s}", end=" | ")
            counts = sorted(lc.keys())
            # sizes = [lc[i + 1] for i in range(max(counts))]
            sizes = [lc[c] for c in counts]
            totalled += sum(sizes)
            # print(
            #     f"{len(sizes):4d} {sum(sizes):8d} {median(sizes):8.0f} {mean(sizes):8.0f}",
            #     end=" | ",
            # )
            # for size in sizes:
            #     print(f"{size:8d}", end="")
            # print()
            # if best is None or len(sizes) > best[1] or median(sizes) > best[5]:
            # if best is None or sum(sizes) > best[2] or median(sizes) > best[5]:
            # if best is None or mean(sizes) > best[4]:
            # if best is None or median(sizes) > best[5]:
            # if best is None or sum(sizes) > best[2] or median(sizes) > best[5]:
            if best is None or len(sizes) > best[1] or max(sizes) > best[3]:
                best = (
                    letter,
                    len(sizes),
                    sum(sizes),
                    max(sizes),
                    mean(sizes),
                    median(sizes),
                )
        print(f"{best=}, {totalled=}")
        cadidates.append(best[0])

    for tag in tags:
        if tag not in cadidates:
            cadidates.append(tag)

    return cadidates


def calculate_tag_splitting(words, dead_letters=None):
    gcounter = defaultdict(lambda: defaultdict(int))
    for word in words:
        dead_word = False
        if dead_letters is not None:
            for dl in dead_letters:
                if dl in word["__counters"] and word["__counters"][dl] > 0:
                    dead_word = True
                    break
        if dead_word:
            continue
        for letter, counter in word["__counters"].items():
            gcounter[letter][counter] += 1
    return gcounter


def read_input(args):

    if args.input == "-":
        infile = sys.stdin
    elif args.input.endswith(".bz2"):
        infile = bz2.BZ2File(args.input)
    else:
        infile = open(args.input)

    words = json.load(infile)

    if args.morph:
        # NZ ~ NVA
        words = filter(
            lambda w: len(set(w["morph"]).intersection(args.morph)) > 0,
            words,
        )

    if args.min_length:
        words = filter(
            lambda w: len(w["word"]) >= args.min_length,
            words,
        )

    if args.no_topo:
        words = filter(
            lambda w: not w.get("topo"),
            words,
        )

    if args.no_nomen:
        words = filter(
            lambda w: not w.get("nomen"),
            words,
        )

    return words if isinstance(words, list) else list(words)


def count_letters(words, args):

    letters = set()
    for i, word in enumerate(words):
        if i % 20000 == 2:
            print(f"{i=} {word=}")
        word["__len"] = len(word["word"])
        w = word["word"] if args.case_sensitive else word["word"].lower()
        if args.tags:
            w = list(filter(lambda c: c in args.tags, w))
        if args.tags_alpha_only is True:
            w = list(filter(lambda c: c.isalpha(), w))
        lcounter = Counter(w)
        word["__counters"] = lcounter
        letters.update(w)

    return words, letters


def count_ranking(words, letters):
    for i, word in enumerate(words):
        lc = word["__counters"]
        word["__ranking"] = [lc.get(c, 0) for c in letters] + [word["__len"]]
    return words


def parse_args():
    parser = argparse.ArgumentParser(description="slovobor db v2 compiler")
    parser.add_argument("input", type=str, default="-", nargs="?")
    parser.add_argument("output", type=str, default="slvbr.db", nargs="?")
    parser.add_argument("--morph", "-m", type=str, default=None)
    parser.add_argument("--no-topo", action="store_true")
    parser.add_argument("--no-nomen", action="store_true")
    parser.add_argument("--case-sensitive", "-cs", action="store_true")
    parser.add_argument("--tags", "-t", type=str, default=None)
    parser.add_argument("--tags-language", "-tl", type=str, default=None)
    parser.add_argument("--tags-alpha-only", "-tao", action="store_true")
    parser.add_argument("--best-tag-order", "-bfo", action="store_true")
    parser.add_argument("--encoding", "-e", type=str, default="utf-8")
    parser.add_argument("--min-length", "-ml", type=int, default=0)
    parser.add_argument("--limit", "-l", type=int, default=0)
    args = parser.parse_args()

    if args.tags_language is not None:
        data = LocaleData(args.tags_language)
        alphabet = data.getExemplarSet()
        args.tags = "".join(sorted(set(alphabet)))
        print(f"{args.tags_language=}→{args.tags=}")

    return args


if __name__ == "__main__":
    main()
