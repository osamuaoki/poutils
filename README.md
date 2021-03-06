# poutils

<!-- vi:se ts=4 sts=4 tw=78 et ai: -->

Osamu Aoki <osamu@debian.org>

This`poutils` provides generic helper programs and utility class to play with
PO files: https://github.com/osamuaoki/poutils

Reverse i18n workflow tools:

* `po_align`: Align msgstr and msgid candidate pairs to the original file
  location with duplicate entries using po4a generated files.  -- align PO
  sequence before po_combine
* `po_combine`: generate a PO file from POT files from the master
  and translation data. --  reverse i18n workflow.  see "po_combine -h"
* `po_clean`: Clean up msgstr matched msgid intelligently (excluding
  <screen>, http...).  -- unset untranslated msgstr intelligently
* `po_check`: check matching between msgid and msgstr in a merged PO file.
  -- sanity check on msgid and msgstr contents.  see "po_check -h"
* `po_rm_fuzzy`: Remove fuzzy from all PO contents -- remove fuzzy flags in PO

GUI/CUI PO editor helper tools: (previous related)

* `po_update`: Update msgstr matching with the previous msgid with the
  updated msgid.-- update not-for-translation msgstr intelligently
* `po_wdiff`: Convert the previous msgid data into the wdiff-like data
   -- easy identification of the upstream changes
* `po_previous`: Revert changes made by `po_wdiff`

## Development of this package

### Git repo usage

* *master* : upstream development with non-native version number
  (This works since I am upstream and maintainer.  See "man dgit-maint-merge")

### Package build

    $ git deborig -f HEAD
    $ debuild

or

    $ ./setup.py deb


