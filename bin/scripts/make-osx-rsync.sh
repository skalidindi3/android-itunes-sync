#!/bin/bash

curl -SO https://download.samba.org/pub/rsync/rsync-3.1.2.tar.gz
curl -SO https://download.samba.org/pub/rsync/rsync-patches-3.1.2.tar.gz
tar -xvf rsync-3.1.2.tar.gz
tar -xvf rsync-patches-3.1.2.tar.gz
rm rsync-3.1.2.tar.gz rsync-patches-3.1.2.tar.gz
patch -p1 < patches/fileflags.diff
patch -p1 < patches/crtimes.diff
patch -p1 < patches/hfs-compression.diff
cd rsync-3.1.2
./prepare-source
./configure
make
