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
def po_check():
    name = "po_check"
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
{0}: check matching between msgid and msgstr in a PO file  Version: {1}

{2}
""".format(
            name, poutils.version, poutils.copyright
        ),
        epilog="See {}(1) manpage for more.".format(name),
    )
    p.add_argument(
        "-f",
        "--force_check",
        action="store_true",
        default=False,
        help="force to check msgstr even for the fuzzy msgstr",
    )
    p.add_argument(
        "-i",
        "--itstool",
        action="store_true",
        default=False,
        help="filter for itstool generated PO file",
    )
    p.add_argument(
        "-r",
        "--raw",
        action="store_true",
        default=False,
        help="raw output without msguniq",
    )
    p.add_argument("po", help="Input PO file name.  Output PO file suffix: .checked")
    args = p.parse_args()
    master = poutils.PotData()
    with open(args.po, "r") as fp:
        master.read_po(file=fp)
    master.check_xml(force_check=args.force_check, itstool=args.itstool)
    with open(args.po + ".checked", "w") as fp:
        master.output_po(file=fp, raw=args.raw)
    return


#######################################################################
if __name__ == "__main__":
    po_check()
