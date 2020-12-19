# poutils

<!-- vi:se ts=4 sts=4 tw=78 et ai: -->

Osamu Aoki <osamu@debian.org>

This `poutils` provides generic helper programs and utility class to play with
PO files:

Reverse i18n workflow tools:

* `po_align`: Align msgstr and msgid pairs to the oroginal file location
  with duplicate entries.  -- align PO sequence before po_combine
* `po_combine`: generate a PO file from POT files from the master
  and translation data. --  reverse i18n workflow.  see "po_combine -h"
* `po_clean`: Clean up msgstr matched msgid intelligently (excluding
  <screen>, http...).  -- unset untranslated msgstr intelligently
* `po_unfuzzy`: Unfazzy all PO contents -- unset fuzzy flags in PO

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
    $ pdebuild

or

    $ ./setup.py deb

## TODO

### PO proofing (po_checkxml)

* XML compliance within msgid/msgstr

    * `<XXX> ... </XXX>` matching
    * `<XXX> ... </XXX>` range overlap
    * `<XXX > or <XXX />` or `</XXX>` only for `<`

* XML tag number matching between msgid/msgstr (if `msgstr != ""`)

    * match the number of `<XXX>`
    * match the number of `</XXX>`
    * match the number of `<XXX />`

