#!/bin/sh
# $Id$

MAJVER=1
MINVER=2
REVISION=1

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

echo "Creating distfile..."
tar -czf $DIR.tar.gz $DIR
tar -cjf $DIR.tar.xz $DIR

echo "Publishing package..."
scp -F /usr/home/ecrist/.ssh/config $DIR.tar.gz $DIR.tar.xz tweak:/usr/home/ftp/pub/FreeBSD/ports/ssl-admin/
scp -F /usr/home/ecrist/.ssh/config $DIR.tar.gz $DIR.tar.xz tweak:/usr/home/ftp/pub/ssl-admin/
scp -F /usr/home/ecrist/.ssh/config $DIR.tar.gz $DIR.tar.xz xxx:/home/ftp/pub/FreeBSD/ports/ssl-admin/
scp -F /usr/home/ecrist/.ssh/config $DIR.tar.gz $DIR.tar.xz xxx:/home/ftp/pub/ssl-admin/

### Update version number in the ports Makefile
echo "Building heirarchy for FreeBSD port build"
rm -rf diff_build/freebsd_port/
svn co http://8.8.178.107/ports/head/security/ssl-admin diff_build/freebsd_port


echo "Auto-modifying support files:"
sed -i -e "s/DISTVERSION=.*$/DISTVERSION=	$MAJVER.$MINVER.$REVISION/" diff_build/freebsd_port/Makefile
LDIR=`pwd`
echo "Building checksum file"
cd diff_build/freebsd_port && make DISTDIR=../../ makesum

echo "Building diff now..."
svn diff
svn diff > ../$MAJVER.$MINVER.$REVISION.patch



