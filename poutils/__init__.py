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
     #  TRANSLATOR-COMMENTS
     #. EXTRACTED-COMMENTS
     #: REFERENCE…
     #, FLAG…
     #| msgid PREVIOUS-UNTRANSLATED-STRING
     msgid UNTRANSLATED-STRING
     msgstr TRANSLATED-STRING
     #~ obsolete data
     WHITE-SPACE
     WHITE-SPACE | EOF
"""
import enum
import sys      # sys.stderr etc.
import re       # for non-greedy {-...-} and {+...+} handling
import tempfile  # for temporary file
import subprocess # for shell pipe
import difflib  # for wdiff
#######################################################################
# Basic constants
#######################################################################
version = '0.1'
copyright = 'Copyright © 2018 Osamu Aoki <osamu@debian.org>'
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
    MSGID = enum.auto()
    MSGSTR = enum.auto()
    BLANK = enum.auto()
    OBSOLETE = enum.auto()

class PotItem:

    def __init__(self):
        self.comment = []
        self.extracted = []
        self.reference = []
        self.flag = []
        self.pmsgid = ""
        self.msgid = ""
        self.msgstr = ""
        self.obsolete = []

    def reset(self):
        self.__init__()

    refuz = re.compile(r'(?P<head>^#,\s*(?:.*,\s*)?)(?P<fuzzy>fuzzy(?:,\s*)?)(?P<tail>.*$)')

    def unfuzzy(self):
        for i, l in enumerate(self.flag):
            if self.refuz.search(l):
                self.flag[i] = self.refuz.sub(r"#, \g<head>\g<tail>", l)
        n = len(self.flag)
        for i in range(n):
            j = n - 1 - i
            if self.flag[j] == '#, ':
                del (self.flag[j])

class PotData():

    def __init__(self):
        self.items = []
        return

    def append(self, item):
        self.items.append(item)
        return

    def read(self, fp):
        item = PotItem()
        j = 0 # line counter
        type = Line.INITIAL                # BEGIN OF FILE
        for l in fp:
            l = l.rstrip() # tailing whitespaces (SP, CR. LF)
            if l == '' and type == Line.BLANK: # WHITE-SPACE
                pass # consecutive Line.BLANK
                #type = Line.BLANK
            elif l == '' and type != Line.INITIAL: # WHITE-SPACE
                self.items.append(item)
                item = PotItem()
                type = Line.BLANK
            elif l[0:2] == '#.':            # EXTRACTED-COMMENTS
                item.extracted.append(l)
                type = Line.EXTRACTED
            elif l[0:2] == '#:':            # REFERENCE…
                item.reference.append(l)
                type = Line.REFERENCE
            elif l[0:2] == '#,':            # FLAG…
                item.flag.append(l)
                type = Line.FLAG
            elif l[0:10] == '#| msgid "':   # msgid PREVIOUS
                item.pmsgid = l[10:-1]
                type = Line.PMSGID
            elif l[0:4] == '#| "' and type == Line.PMSGID:
                item.pmsgid += l[4:-1]
                #type = Line.PMSGID
            elif l[0:2] == "#~" and type == Line.BLANK:     # OBSOLETE
                item.obsolete.append(l)
                type = Line.OBSOLETE
            elif l[0:2] == "#~" and type == Line.OBSOLETE:   # OBSOLETE
                item.obsolete.append(l)
                #type = Line.OBSOLETE
            elif l[0:1] == '#':             # TRANSLATOR-COMMENT
                item.comment.append(l)
                type = Line.COMMENT
            elif l[0:7] == 'msgid "':       # msgid STRING
                item.msgid = l[7:-1]
                type = Line.MSGID
            elif l[0:8] == 'msgstr "':      # msgstr STRING
                item.msgstr = l[8:-1]
                type = Line.MSGSTR
            elif l[0:1] == '"' and type == Line.MSGID:
                item.msgid += l[1:-1]
                # type = Line.MSGID
            elif l[0:1] == '"' and type == Line.MSGSTR:
                item.msgstr += l[1:-1]
                # type = Line.MSGSTR
            else:                          # ILLEGAL
                print("ERROR at {} parsing '{}' as {}".format(j, l, type))
                exit
            print("I {}: {} '{}'".format(j, type, l))
            j += 1
        if type != Line.BLANK:
            self.items.append(item)
        return

    def output_raw(self, fp):
        for item in self.items:
            if len(item.obsolete) == 0:
                for l in item.comment:
                    print(l, file=fp)
                for l in item.extracted:
                    print(l, file=fp)
                for l in item.reference:
                    print(l, file=fp)
                for l in item.flag:
                    print(l, file=fp)
                if item.pmsgid != '':
                    print('#| msgid "' + item.pmsgid + '"', file=fp)
                print('msgid "' + item.msgid + '"', file=fp)
                print('msgstr "' + item.msgstr + '"', file=fp)
            else:
                for l in item.obsolete:
                    print(l, file=fp)
            print("", file=fp)
        return

    def output(self, fp, wrap=True):
        if wrap:
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as ftmp:
                self.output_raw(ftmp)
                ftmp.seek(0)
                subprocess.run(["msgcat", "-"], stdin=ftmp, stdout=fp, stderr=sys.stderr, encoding="utf-8")
        else:
            self.output_raw(fp)
        return

    def clean_msgstr(self, pattern_extracted=None, pattern_msgid=None):
        """
        Clean msgstr if msgid is the same except for pattern matches
        """
        if pattern_extracted:
            re_pattern_extracted =  re.compile(pattern_extracted)
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
                    else:
                        item.msgstr = ""
                        continue
                else:
                    item.msgstr = ""
        return

    def dup_msgstr(self, pattern_extracted=None, pattern_msgid=None, unfuzzy=True):
        """
        Duplicate msgid as msgstr for pattern matches
        """
        if pattern_extracted:
            re_pattern_extracted =  re.compile(pattern_extracted)
        if pattern_msgid:
            re_pattern_msgid = re.compile(pattern_msgid)
        for item in self.items:
            if pattern_msgid and re_pattern_msgid.search(item.msgid):
                item.msgstr = item.msgid
                item.unfuzzy()
            elif pattern_extracted:
                for l in item.extracted:
                    if re_pattern_extracted.search(l):
                        item.msgstr = item.msgid
                        item.unfuzzy()
        return

    def wdiff_msgid(self):
        re_escape =  re.compile(r'(\{)(\+|-)|(-|\+)(\})')
        for item in self.items:
            if item.pmsgid != "" and \
                    item.pmsgid[0:12] != "{++}{--}(++}" and \
                    item.pmsgid[-12:] != "{++}{--}(++}":
                wdiff = ""
                # Protect any occurrence of {+ +} {- -} by adding {++} in each of them
                item.pmsgid = re_escape.sub(r'\g<1>\g<3>{++}\g<2>\g<4>', item.pmsgid)
                diff=difflib.SequenceMatcher(isjunk=None,a=item.pmsgid,b=item.msgid)
                for tag, i1, i2, j1, j2 in diff.get_opcodes():
                    if tag == "equal":
                        wdiff += item.pmsgid[i1:i2]
                    elif tag == "delete":
                        wdiff += '{-' + item.pmsgid[i1:i2] + '-}'
                    elif tag == "insert":
                        wdiff += '{+' + item.msgid[j1:j2] + '+}'
                    elif tag == "replace":
                        wdiff += '{-' + item.pmsgid[i1:i2] + '-}{+' +item.msgid[j1:j2] + '+}'
                # {++}{--}(++}"s placed around the wdiff string are NOP for change.
                # These are used as the indicator for wdiff content.
                item.pmsgid = '{++}{--}(++}' + wdiff + '{++}{--}(++}'
        return

    def previous_msgid(self):
        re_added =  re.compile(r'(\{\+)(.*?)(\+\})')
        re_deleted = re.compile(r'(\{-)(.*?)(-\})')
        for item in self.items:
            if item.pmsgid != "" and \
                    item.pmsgid[0:12] == '{++}{--}(++}' and \
                    item.pmsgid[-12:] == '{++}{--}(++}':
                previous = item.pmsgid[12:-12]
                previous = re_added.sub("", previous)           # Drop {+...+}
                previous = re_deleted.sub(r'\g<2>', previous)   # Keep ... of  {-...-}
                item.pmsgid = previous
        return

    def update_msgstr(self):
        self.previous_msgid()
        for item in self.items:
            if item.pmsgid == item.msgstr:
                item.msgstr = item.msgid
                item.pmsgid = ""
                item.unfuzzy()

    def normalize(self, keep_last_extracted=True, drop_comment=True, \
            drop_reference=True,  drop_flag=True, \
            drop_pmsgid=True, drop_obsolete=True):
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
                print("len(extracted)={} for msgid={}".format(len(item.extracted), item.msgid))
            if len(item.extracted) == 0:
                item.extracted = [ '#.' ]
            else:
                if keep_last_extracted:
                    item.extracted = [item.extracted[-1]]
                else:
                    item.extracted = [item.extracted[0]]
        if drop_obsolete:
            n = len(self.items)
            for i in range(n):
                j = n - 1 - i
                if self.items[j].msgid == '' and self.items[j].msgstr == '' and len(self.items[j].obsolete) == 0:
                    del (self.items[j])
                
    def normalize_extracted(self, keep_last_extracted=True):
        self.normalize(keep_last_extracted=keep_last_extracted, \
                drop_comment=False, \
                drop_reference=False,  drop_flag=False, \
                drop_pmsgid=False, drop_obsolete=False)
        return

    def combine_pots(self, translation, check_extracted=False):
        for i, item in enumerate(self.items):
            if i >= len(translation.items):
                break
            if item.msgid == "":
                item.msgstr = translation.items[i].msgstr
            else:
                if not check_extracted or \
                    ( not item.extracted and not translation.items[i].extracted ) or \
                    item.extracted and translation.items[i].extracted and \
                   item.extracted[0] == translation.items[i].extracted[0]:
                    item.msgstr = translation.items[i].msgid
                else:
                    print("E: *** master: {} != translation: {} ***".format(item.extracted[0], translation.items[i].extracted[0]))
                    break
        if len(self.items) > len(translation.items):
            print("E: *** master: {} > translation: {} ***".format(len(self.items), len(translation.items)))
        if len(self.items) < len(translation.items):
            print("E: *** master: {} < translation: {} ***".format(len(self.items), len(translation.items)))
        return

#######################################################################
# This program functions differently if called via symlink
#######################################################################
if __name__ == '__main__':
    pots = PotData()
    with open("de.po") as fp:
        pots.read(fp)
    for i in range(0,5):
        item = PotItem()
        item.msgid = "FOO ID xxxxxx xxxxxxxxxxxxxxxxxx {}".format(i)
        item.msgstr = "FOO STR zzzzzzzzzzzzzzzzzzzzzzz {}".format(i)
        pots.append(item)
    pots.normalize_extracted()
    pots.output_raw(sys.stdout)
