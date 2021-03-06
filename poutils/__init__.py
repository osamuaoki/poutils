#!/usr/bin/python3
# vim:se tw=0 sts=4 ts=4 et ai:
"""
Copyright © 2018 Osamu Aoki

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

This scripts work on PO/POT file having a repeat of the following structure

     WHITE-SPACE | BOF
   ? #  TRANSLATOR-COMMENTS
   ? #. EXTRACTED-COMMENTS
   ? #: REFERENCE…
   ? #, FLAG…
   ? #| msgid PREVIOUS-UNTRANSLATED-STRING
   ? msgctxt "_"
     msgid UNTRANSLATED-STRING
     msgstr TRANSLATED-STRING
   ? #~ obsolete data
   ? WHITE-SPACE
   ? WHITE-SPACE | EOF
"""
import enum
import sys  # sys.stderr etc.
import re  # for non-greedy {-...-} and {+...+} handling
import tempfile  # for temporary file
import subprocess  # for shell pipe
import difflib  # for wdiff
import xml.etree.ElementTree as ET
import itertools as IT
import io
import codecs

#######################################################################
# Basic constants
#######################################################################
version = "0.3"
copyright = "Copyright © 2018 -2021 Osamu Aoki <osamu@debian.org>"
#######################################################################
# Basic Class to handle POT/PO data
#######################################################################
class Line(enum.Enum):
    INITIAL = enum.auto()
    COMMENT = enum.auto()
    EXTRACTED = enum.auto()
    REFERENCE = enum.auto()
    FLAG = enum.auto()
    PMSGID = enum.auto()
    MSGCTXT = enum.auto()
    MSGID = enum.auto()
    MSGSTR = enum.auto()
    BLANK = enum.auto()
    OBSOLETE = enum.auto()


class PotItem:
    def __init__(self):
        self.syncid = -1
        self.comment = []
        self.extracted = []
        self.reference = []
        self.index = []
        self.number_ref = 0
        self.flag = []
        self.pmsgid = ""
        self.msgctxt = ""
        self.msgid = ""
        self.msgstr = ""
        self.obsolete = []

    def reset(self):
        self.__init__()

    refuz = re.compile(
        r"(?P<head>^#,\s*(?:.*,\s*)?)(?P<fuzzy>fuzzy(?:,\s*)?)(?P<tail>.*$)"
    )

    def is_fuzzy(self):
        flag = False
        for l in self.flag:
            if self.refuz.search(l):
                flag = True
                break
        return flag

    def rm_fuzzy(self):
        for i, l in enumerate(self.flag):
            if self.refuz.search(l):
                self.flag[i] = self.refuz.sub(r"#, \g<head>\g<tail>", l)
        n = len(self.flag)
        for i in range(n):
            j = n - 1 - i  # trim from tail side of list
            if self.flag[j] == "#, ":
                del self.flag[j]

    def add_fuzzy(self):
        n = len(self.flag)
        if n == 0:
            self.flag = ["#, fuzzy"]
        elif not self.is_fuzzy():
            print("n={}, flag[n-1]={}".format(n, self.flag[n - 1]))
            self.flag[n - 1] = "#, fuzzy" + self.flag[n - 1][1:]
        return

    reindex = re.compile(r"[^:]*:")

    def set_index(self):
        # parse po4a-gettextize '#: ' lead reference lines
        refs = []
        for l in self.reference:
            refs.extend(l[3:].split(" "))
        if refs == []:
            self.index.append(-1)
        else:
            for r in refs:
                self.index.append(int(self.reindex.sub("", r)))

    def set_syncid(self, sid):
        self.syncid = sid


class PotData:
    def __init__(self):
        self.items = []
        return

    def __getitem__(self, i):
        return self.items[i]

    def __iter__(self):
        yield from self.items

    def __len__(self):
        return len(self.items)

    def append(self, item):
        self.items.append(item)
        return

    def read_po(self, file=sys.stdin, verbose=False):
        item = PotItem()
        j = 0  # line counter
        type = Line.INITIAL  # BEGIN OF FILE
        for l in file:
            l = l.rstrip()  # tailing whitespaces (SP, CR. LF)
            if l == "" and type == Line.BLANK:  # WHITE-SPACE
                # consecutive Line.BLANK
                # type = Line.BLANK
                pass
            elif l == "" and type != Line.INITIAL:  # WHITE-SPACE
                self.items.append(item)
                item = PotItem()
                type = Line.BLANK
            elif l[0:2] == "#.":  # EXTRACTED-COMMENTS
                item.extracted.append(l)
                type = Line.EXTRACTED
            elif l[0:2] == "#:":  # REFERENCE…
                item.reference.append(l)
                item.number_ref += len(l[3:].split(" "))
                type = Line.REFERENCE
            elif l[0:2] == "#,":  # FLAG…
                item.flag.append(l)
                type = Line.FLAG
            elif l[0:10] == '#| msgid "':  # msgid PREVIOUS
                item.pmsgid = l[10:-1]
                type = Line.PMSGID
            elif l[0:4] == '#| "' and type == Line.PMSGID:
                item.pmsgid += l[4:-1]
                # type = Line.PMSGID
            elif l[0:2] == "#~" and type == Line.BLANK:  # OBSOLETE
                item.obsolete.append(l)
                type = Line.OBSOLETE
            elif l[0:2] == "#~" and type == Line.OBSOLETE:  # OBSOLETE
                item.obsolete.append(l)
                # type = Line.OBSOLETE
            elif l[0:1] == "#":  # TRANSLATOR-COMMENT
                item.comment.append(l)
                type = Line.COMMENT
            elif l[0:9] == 'msgctxt "':  # msgctxt STRING
                item.msgctxt = l[9:-1]
                type = Line.MSGCTXT
            elif l[0:7] == 'msgid "':  # msgid STRING
                item.msgid = l[7:-1]
                type = Line.MSGID
            elif l[0:8] == 'msgstr "':  # msgstr STRING
                item.msgstr = l[8:-1]
                type = Line.MSGSTR
            elif l[0:1] == '"' and type == Line.MSGID:
                item.msgid += l[1:-1]
                # type = Line.MSGID
            elif l[0:1] == '"' and type == Line.MSGSTR:
                item.msgstr += l[1:-1]
                # type = Line.MSGSTR
            else:  # ILLEGAL
                print("ERROR at {} parsing '{}' as {}".format(j, l, type))
                exit
            if verbose:
                print("I {}: {} '{}'".format(j, type, l))
            j += 1
        if type != Line.BLANK:
            self.items.append(item)
        return

    def set_all_index(self):
        for item in self.items:
            item.set_index()

    def set_all_syncid(self):
        for sid, item in enumerate(self.items):
            item.set_syncid(sid)

    def output_raw(self, file=sys.stdout):
        for item in self.items:
            if len(item.obsolete) == 0:
                if item.syncid >= 0:
                    print("# SYNC1: {:0>8}".format(item.syncid), file=file)
                    print("# SYNC2: {:0>8}".format(item.syncid), file=file)
                    print("# SYNC3: {:0>8}".format(item.syncid), file=file)
                    print("# SYNC4: {:0>8}".format(item.syncid), file=file)
                    print("# SYNC5: {:0>8}".format(item.syncid), file=file)
                for l in item.comment:
                    print(l, file=file)
                for l in item.extracted:
                    print(l, file=file)
                for l in item.reference:
                    print(l, file=file)
                for l in item.flag:
                    print(l, file=file)
                if item.pmsgid != "":
                    print('#| msgid "' + item.pmsgid + '"', file=file)
                if item.msgctxt:
                    print('msgctxt "' + item.msgctxt + '"', file=file)
                    print('msgid "' + item.msgid + '"', file=file)
                    print('msgstr "' + item.msgstr + '"', file=file)
                elif item.msgid or item.msgstr:
                    # printing msgid and msgstr if both of them are not ""
                    print('msgid "' + item.msgid + '"', file=file)
                    print('msgstr "' + item.msgstr + '"', file=file)
            else:
                for l in item.obsolete:
                    print(l, file=file)
            print("", file=file)
        return

    def output_po(self, file=sys.stdout, raw=False):
        if raw:
            self.output_raw(file=file)
        else:
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as ftmp:
                self.output_raw(file=ftmp)
                ftmp.seek(0)
                subprocess.run(
                    ["msguniq", "--use-first", "-"],
                    stdin=ftmp,
                    stdout=file,
                    stderr=sys.stderr,
                    encoding="utf-8",
                )
        return

    def rm_fuzzy_all(self):
        """
        remove fuzzy for all PO contents
        """
        for item in self.items:
            item.rm_fuzzy()
        return

    def clean_msgstr(
        self, pattern_extracted=None, pattern_msgid=None, keep_fuzzy=False
    ):
        """
        Clean msgstr if msgid is the same except for pattern matches
        """
        if pattern_extracted:
            re_pattern_extracted = re.compile(pattern_extracted)
        if pattern_msgid:
            re_pattern_msgid = re.compile(pattern_msgid)
        for item in self.items:
            if item.msgid == item.msgstr:
                if pattern_msgid and re_pattern_msgid.search(item.msgid):
                    pass
                elif pattern_extracted:
                    for l in item.extracted:
                        if re_pattern_extracted.search(l):
                            break
                    else:  # pattern_extracted not found
                        item.msgstr = ""
                    if not keep_fuzzy:
                        item.rm_fuzzy()
                else:
                    item.msgstr = ""
                    if not keep_fuzzy:
                        item.rm_fuzzy()
            else:
                pass
        return

    def check_xml(self, force_check=False, itstool=False):
        """
        check matching xml tags between msgid and msgstr in a merged PO file.
        """
        reitstool = re.compile("<_:")
        for item in self.items:
            if not item.is_fuzzy() or force_check:
                # trick to evaluate escape sequence: https://stackoverflow.com/questions/4020539/process-escape-sequences-in-a-string-in-python
                msgid = codecs.escape_decode(bytes(item.msgid.strip(), "utf-8"))[
                    0
                ].decode("utf-8")
                if itstool:
                    msgid = reitstool.sub("<", msgid)
                # print("msgid={}".format(msgid))
                msgstr = codecs.escape_decode(bytes(item.msgstr.strip(), "utf-8"))[
                    0
                ].decode("utf-8")
                if itstool:
                    msgstr = reitstool.sub("<", msgstr)
                # print("msgstr={}".format(msgstr))
                # make minimal XML from PO strings
                xmsgid = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n<xml>\n'
                    + msgid
                    + "\n</xml>"
                )
                xmsgstr = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n<xml>\n'
                    + msgstr
                    + "\n</xml>"
                )
                if msgid and not item.msgctxt:
                    try:
                        etid = ET.fromstring(xmsgid)
                    except ET.ParseError as err:
                        lineno, col = err.position
                        line = next(IT.islice(io.StringIO(xmsgid), lineno - 1, lineno))
                        item.comment.append(
                            "# !!! WARN !!!: XML TAG parse error in msgid"
                        )
                        item.comment.append("#       {}".format(err.msg))
                        item.comment.append("#       {}".format(line.rstrip()))
                        item.comment.append("#       {:=>{}}".format("^", col))
                        item.add_fuzzy()
                        id_tags = []
                    else:
                        id_tags = [elem.tag for elem in etid.iter()]
                        id_tags.sort()
                else:
                    id_tags = []
                if msgid and msgstr and not item.msgctxt:
                    try:
                        etstr = ET.fromstring(xmsgstr)
                    except ET.ParseError as err:
                        lineno, col = err.position
                        line = next(IT.islice(io.StringIO(xmsgstr), lineno - 1, lineno))
                        item.comment.append(
                            "# !!! WARN !!!: XML TAG parse error in msgstr"
                        )
                        item.comment.append("#       {}".format(err.msg))
                        item.comment.append("#       {}".format(line.rstrip()))
                        item.comment.append("#       {:=>{}}".format("^", col))
                        item.add_fuzzy()
                        str_tags = []
                    else:
                        str_tags = [elem.tag for elem in etstr.iter()]
                        str_tags.sort()
                else:
                    str_tags = []
                if id_tags and str_tags:
                    if id_tags != str_tags:
                        item.comment.append(
                            "# !!! WARN !!!: XML TAG mismatch between msgid and msgstr"
                        )
                        item.comment.append(
                            "#       msgid  = {}".format(",".join(id_tags))
                        )
                        item.comment.append(
                            "#       msgstr = {}".format(",".join(str_tags))
                        )
                        item.add_fuzzy()
        return

    def dup_msgstr(self, pattern_extracted=None, pattern_msgid=None, rm_fuzzy=True):
        """
        Duplicate msgid as msgstr for pattern matches
        """
        # No pre-made command provided.
        # Call from your custom command to add duplicate msgstr to matched items
        if pattern_extracted:
            re_pattern_extracted = re.compile(pattern_extracted)
        if pattern_msgid:
            re_pattern_msgid = re.compile(pattern_msgid)
        for item in self.items:
            if pattern_msgid and re_pattern_msgid.search(item.msgid):
                item.msgstr = item.msgid
                if rm_fuzzy:
                    item.rm_fuzzy()
            elif pattern_extracted:
                for l in item.extracted:
                    if re_pattern_extracted.search(l):
                        item.msgstr = item.msgid
                        if rm_fuzzy:
                            item.rm_fuzzy()
            else:
                pass
        return

    def wdiff_msgid(self):
        re_escape = re.compile(r"(\{)(\+|-)|(-|\+)(\})")
        for item in self.items:
            if (
                item.pmsgid != ""
                and item.pmsgid[0:12] != "{++}{--}(++}"
                and item.pmsgid[-12:] != "{++}{--}(++}"
            ):
                wdiff = ""
                # Protect any occurrence of {+ +} {- -} by adding {++} in each of them
                item.pmsgid = re_escape.sub(r"\g<1>\g<3>{++}\g<2>\g<4>", item.pmsgid)
                diff = difflib.SequenceMatcher(isjunk=None, a=item.pmsgid, b=item.msgid)
                for tag, i1, i2, j1, j2 in diff.get_opcodes():
                    if tag == "equal":
                        wdiff += item.pmsgid[i1:i2]
                    elif tag == "delete":
                        wdiff += "{-" + item.pmsgid[i1:i2] + "-}"
                    elif tag == "insert":
                        wdiff += "{+" + item.msgid[j1:j2] + "+}"
                    elif tag == "replace":
                        wdiff += (
                            "{-"
                            + item.pmsgid[i1:i2]
                            + "-}{+"
                            + item.msgid[j1:j2]
                            + "+}"
                        )
                # {++}{--}(++}"s placed around the wdiff string are NOP for change.
                # These are used as the indicator for wdiff content.
                item.pmsgid = "{++}{--}(++}" + wdiff + "{++}{--}(++}"
        return

    def previous_msgid(self):
        re_added = re.compile(r"(\{\+)(.*?)(\+\})")
        re_deleted = re.compile(r"(\{-)(.*?)(-\})")
        for item in self.items:
            if (
                item.pmsgid != ""
                and item.pmsgid[0:12] == "{++}{--}(++}"
                and item.pmsgid[-12:] == "{++}{--}(++}"
            ):
                previous = item.pmsgid[12:-12]
                previous = re_added.sub("", previous)  # Drop {+...+}
                previous = re_deleted.sub(r"\g<2>", previous)  # Keep ... of  {-...-}
                item.pmsgid = previous
        return

    def update_msgstr(self):
        self.previous_msgid()
        for item in self.items:
            if item.pmsgid == item.msgstr:
                item.msgstr = item.msgid
                item.pmsgid = ""
                item.rm_fuzzy()

    def normalize(
        self,
        keep_last_extracted=True,
        drop_comment=True,
        drop_reference=True,
        drop_flag=True,
        drop_pmsgid=True,
        drop_obsolete=True,
    ):
        for item in self.items:
            if drop_comment:
                item.comment = []
            if drop_reference:
                item.reference = []
            if drop_flag:
                item.flag = []
            if drop_pmsgid:
                item.pmsgid = ""
            if drop_obsolete:
                item.obsolete = []
            if len(item.extracted) > 1:
                print(
                    "len(extracted)={} for msgid={}".format(
                        len(item.extracted), item.msgid
                    )
                )
            if len(item.extracted) == 0:
                item.extracted = ["#."]
            else:
                if keep_last_extracted:
                    item.extracted = [item.extracted[-1]]
                else:
                    item.extracted = [item.extracted[0]]
        if drop_obsolete:
            n = len(self.items)
            for i in range(n):
                j = n - 1 - i
                if (
                    self.items[j].msgid == ""
                    and self.items[j].msgstr == ""
                    and len(self.items[j].obsolete) == 0
                ):
                    del self.items[j]

    def normalize_extracted(self, keep_last_extracted=True):
        self.normalize(
            keep_last_extracted=keep_last_extracted,
            drop_comment=False,
            drop_reference=False,
            drop_flag=False,
            drop_pmsgid=False,
            drop_obsolete=False,
        )
        return

    def combine_pots(self, translation):
        if len(self.items) > len(translation.items):
            print(
                """\
E: *** master: {} > translation: {} ***

   Different strings (msgid) in master may be translated into
   a same string (msgstr) in translation.

   This often happens when capitalization or any trivial
   typographical differences in master are merged into
   a same translated string in translation.

   Use po_align to ensure easier matching (for po4a).

   Also, if the translation misses some tags such as
   <_:footnote-1/>, then alignment becomes broken.

""".format(
                    len(self.items), len(translation.items)
                )
            )
        if len(self.items) < len(translation.items):
            print(
                """\
E: *** master: {} < translation: {} ***

   A same string (msgid) in master may be translated into
   different strings (msgstr) in translation.

""".format(
                    len(self.items), len(translation.items)
                )
            )
        num_warn_extracted = 0
        num_warn_ref = 0
        j = 0
        for item in self.items:
            if j >= len(translation.items):
                break
            if item.msgid == "":
                # header part
                item.msgstr = translation.items[j].msgstr
                j += 1
            else:
                # normal part
                if item.number_ref != translation.items[j].number_ref:
                    num_warn_ref += 1
                    item.reference.append(
                        "# WARN: mismatched references: {} --> {}".format(
                            item.number_ref, translation.items[j].number_ref
                        )
                    )
                    item.reference.extend(translation.items[j].reference)
                if item.extracted[0] != translation.items[j].extracted[0]:
                    num_warn_extracted += 1
                    item.extracted.append("# WARN: mismatched extracted tag pattern")
                    item.extracted.extend(translation.items[j].extracted)
                item.msgstr = translation.items[j].msgid
                j += 1
        if num_warn_extracted > 0:
            print(
                "W: *** mismatched extracted tag pattern: {}".format(num_warn_extracted)
            )
        if num_warn_ref > 0:
            print("W: *** mismatched references: {}".format(num_warn_ref))
        return


#######################################################################
if __name__ == "__main__":
    pots = PotData()
    with open("de.po") as fp:
        pots.read_po(file=fp)
    for i in range(0, 5):
        item = PotItem()
        item.msgid = "FOO ID xxxxxx xxxxxxxxxxxxxxxxxx {}".format(i)
        item.msgstr = "FOO STR zzzzzzzzzzzzzzzzzzzzzzz {}".format(i)
        pots.append(item)
    pots.normalize_extracted()
    pots.output_raw(file=sys.stdout)
