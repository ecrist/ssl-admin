#!/bin/sh
# $Id$

MAJVER=1
MINVER=3
REVISION=0

DIR=ssl-admin-$MAJVER.$MINVER.$REVISION


## Make directory - if it's there, delete it so we can start fresh.
if [ -d $DIR ]; then
	rm -rf $DIR
fi
mkdir $DIR

echo "Updating version string"
sed -i -e "s/~~~VERSION~~~/$MAJVER.$MINVER.$REVISION/" ssl-admin

## Copy file over.
cp -r man1 man5 Makefile configure openssl.conf ssl-admin ssl-admin.conf $DIR

## remove .svn dir, if it exists.
find $DIR -type d -name .svn | xargs rm -rf  
find $DIR -type d -name .git | xargs rm -rf  

echo "Creating distfile..."
tar -czf $DIR.tar.gz $DIR
tar -cjf $DIR.tar.xz $DIR
