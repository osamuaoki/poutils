#!/usr/bin/python3
# vi:se ts=4 sts=4 et ai:
# Template from
# https://packaging.python.org/tutorials/packaging-projects/
import setuptools
from distutils.command.clean import clean as distutils_clean

import subprocess
import os
import sys
import shutil
import re

# import locally
import poutils

class distclean(distutils_clean):
    description = "clean up all files from 'build' and 'dist' command"
    def run(self):
        if self.dry_run:
            return
        subprocess.call('rm -rf build dist poutils/__pycache__ poutils.egg-info', shell=True)
        subprocess.call('rm -f poutils/poutils MANIFEST', shell=True)

class deb(distclean):
    description = "Make versioned Debian source tree and upstream tarball."
    def run(self):
        if self.dry_run:
            return
        distclean.run(self)
        if not os.path.isfile('debian/rules'):
            print('E: Missing debian/rules', file=sys.stderr)
            exit(1)
        elif not os.path.isfile('debian/control'):
            print('E: Missing debian/control', file=sys.stderr)
            exit(1)
        elif not os.path.isfile('debian/changelog'):
            print('E: Missing debian/changelog', file=sys.stderr)
            exit(1)
        else:
            with open('debian/changelog', mode='r', encoding='utf-8') as f:
                line = f.readline()
            pkgver = re.match('([^ \t]+)[ \t]+\(([^()]+)-([^-()]+)\)', line)
            if pkgver:
                package = pkgver.group(1).lower()
                version = pkgver.group(2)
                revision = pkgver.group(3)
            else:
                print('E: changelog start with "{}"'.format(line), file=sys.stderr)
                exit(1)
        if poutils.version != version:
            print('E: Update version in poutils/__init__.py to "{}"'.format(version), file=sys.stderr)
            exit(1)
        parent_path = os.path.dirname(os.path.abspath(__file__))
        parent = os.path.basename(parent_path)
        if parent != package and parent[:len(package)+1] == package + '-':
            pint('E: Git repo directory can\'t use versioned name directory', file=sys.stderr)
            exit(1)
        # remove existing source_tree
        source = package + '-' + version
        tarball = package + '_' + version + '.orig.tar.xz'
        source_path = parent_path + '/' + source
        if os.path.exists(source_path):
            shutil.rmtree(source_path)
        # move to parent directory
        # copy from parent to source using hardlinks excluding .git
        os.chdir('..')
        command = "rsync -av --exclude=.git --link-dest='" + parent_path + "' '" + parent + "/.' '" + source + "'"
        print('I: $ {}'.format(command), file=sys.stderr)
        if subprocess.call(command, shell=True) != 0:
            print('E: rsync -av failed.', file=sys.stderr)
            exit(1)
        # tar while excluding debian directories
        command = 'tar --exclude=\'' + source + '/debian\' --anchored --xz -cvf '
        command += tarball + ' ' + source
        print('I: $ {}'.format(command), file=sys.stderr)
        if subprocess.call(command, shell=True) != 0:
            print('E: tar failed {}.'.format(tarball), file=sys.stderr)
            exit(1)
        print('I: {} tarball made'.format(tarball), file=sys.stderr)
        os.chdir(source)
        print('I: please run pdebuild/debuild in {}'.format('../' + source), file=sys.stderr)
        print('I: please run gbp import-dsc ../*.dsc', file=sys.stderr)

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="poutils",
    version="0.0.1",
    author="Osamu Aoki",
    author_email="osamu@debian.org",
    description="Utility for PO file",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/osamuaoki/poutils",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': [
            'po_combine=poutils.po_combine:po_combine',
            'po_clean=poutils.po_clean:po_clean',
            'po_update=poutils.po_update:po_update',
            'po_wdiff=poutils.po_wdiff:po_wdiff',
            'po_previous=poutils.po_previous:po_previous',
        ],
    },
    cmdclass = {'distclean': distclean, 'deb': deb}
)


