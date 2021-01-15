#!/usr/bin/python3
# vim:se tw=0 sts=4 ts=4 et ai:
"""
Copyright © 2020 Osamu Aoki

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
import os  # for os.path.basename etc.
import sys  # sys.stderr etc.
import shutil
import copy

# To test this in place, setup a symlink with "ln -sf . poutils"
import poutils

#######################################################################
# main program
#######################################################################
def po_align():
    name = "po_align"
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
{0}: align PO file contents according to the original file location            Version: {1}

{2}
""".format(
            name, poutils.version, poutils.copyright
        ),
        epilog="See {}(1) manpage for more.".format(name),
    )
    p.add_argument("po", help="Input PO file name.  Output PO file suffix: .aligned")
    args = p.parse_args()
    master = poutils.PotData()
    with open(args.po, "r") as fp:
        master.read_po(file=fp)
    master.set_all_index()
    index_map = []
    for j, item in enumerate(master):
        for i in item.index:
            index_map.append((i, j))
    index_map.sort()
    aligned = poutils.PotData()
    for i, j in index_map:
        aligned.append(copy.copy(master[j]))
    aligned.set_all_syncid()
    with open(args.po + ".aligned", "w") as fp:
        # Never use msguniq here
        aligned.output_raw(file=fp)
    return


#######################################################################
if __name__ == "__main__":
    po_align()
