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
"""
import argparse
import sys  # sys.stderr etc.
import shutil
import os  # for os.path.basename etc.

# To test this in place, setup a symlink with "ln -sf . poutils"
import poutils

#######################################################################
# main program
#######################################################################
def po_clean():
    name = "po_clean"
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
{0}: make a PO file clean by removing identical ones as msgid  Version: {1}

{2}
""".format(
            name, poutils.version, poutils.copyright
        ),
        epilog="See {}(1) manpage for more.".format(name),
    )
    p.add_argument(
        "-k",
        "--keep_fuzzy",
        action="store_true",
        default=False,
        help="keep all fuzzy markers",
    )
    p.add_argument(
        "-r",
        "--raw",
        action="store_true",
        default=False,
        help="raw output without uniq",
    )
    p.add_argument("po", help="Input PO file name.  Output PO file suffix: .cleaned")
    args = p.parse_args()
    master = poutils.PotData()
    with open(args.po, "r") as fp:
        master.read_po(file=fp)
    master.clean_msgstr(
        pattern_extracted=r"<screen>",
        pattern_msgid=r"^https?://",
        keep_fuzzy=args.keep_fuzzy,
    )
    with open(args.po + ".cleaned", "w") as fp:
        master.output_po(file=fp, raw=args.raw)
    return


#######################################################################
if __name__ == "__main__":
    po_clean()
