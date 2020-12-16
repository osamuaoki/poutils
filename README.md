# poutils

<!-- vi:se ts=4 sts=4 tw=78 et ai: --> 

Osamu Aoki <osamu@debian.org>

This `poutils` provides generic helper programs and utility class to play with
PO files:

* `po_clean`: Clean up msgstr matched msgid intelligently (excluding
  <screen>, http...).  -- unset untranslated msgstr intelligently
* `po_update`: Update msgstr matching with the previous msgid with the
  updated msgid.-- update not-for-translation msgstr ntelligently
* `po_combine`: generate a PO file from POT files from the master
  and translation data. --  reverse i18n workflow.  see "po_combine -h"
* `po_wdiff`: Convert the previous msgid data into the wdiff-like data
   -- easy identification of the upstream changes
* `po_previous`: Revert changes made by `po_wdiff`

## Development of this package

### Git repo usage

debian/gbp.conf is set for:

* *master* : upstream development (quasi-native style with debian/*)
* *upstream* : upstream tarball (gbp import-dsc)
* *debian* : Debian source tree non-native style (gbp import-dsc)
* *pristine-tar* : pristine-tar of upstream tarball (gbp import-dsc)

### Package build

    $ python3 setup.py deb
    $ cd ../poutils-0.*
    $ pdebuild

