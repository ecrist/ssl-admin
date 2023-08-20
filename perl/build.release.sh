#!/bin/sh
#
# This script prepares a package file (both tgz and xz) which can
# be used to build OS-specific packages.

MAJVER=1
MINVER=3
REVISION=0

DIR=ssl-admin-$MAJVER.$MINVER.$REVISION


## Make directory - if it's there, delete it so we can start fresh.
if [ -d $DIR ]; then
	rm -rf $DIR
fi
mkdir "$DIR"

## Copy file over.
cp -r man1 man5 Makefile configure openssl.conf ssl-admin ssl-admin.conf "$DIR"

echo "Updating version string"
sed -i -e "s/~~~VERSION~~~/$MAJVER.$MINVER.$REVISION/" "$DIR/ssl-admin"

## remove .svn and .git dirs, if they exist.
find $DIR -type d -name .svn | xargs rm -rf  
find $DIR -type d -name .git | xargs rm -rf  

echo "Creating distfile..."
tar -czf $DIR.tar.gz $DIR
tar -cjf $DIR.tar.xz $DIR
