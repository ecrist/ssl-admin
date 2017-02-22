# ssl-admin Makefile
# $Id: Makefile 366 2014-10-01 17:44:18Z ecrist $
 
ETCDIR?=VARETC
BINDIR?=VARBIN
MANDIR?=VARMAN
SED_CMD?=VARSED

all:

build-devel:

	[ -e "working-build/" ] || mkdir -p working-build/ssl-admin
	${SED_CMD} s+~~~ETCDIR~~~+${ETCDIR}+g man1/ssl-admin.1 > working-build/ssl-admin.1
	${SED_CMD} s+~~~ETCDIR~~~+${ETCDIR}+g man5/ssl-admin.conf.5 > working-build/ssl-admin.conf.5
	install -c -m 0660 -S -v ssl-admin.conf working-build/ssl-admin/ssl-admin.conf
	install -c -m 0660 -S -v openssl.conf working-build/ssl-admin/openssl.conf
	${SED_CMD} -e "s+~~~ETCDIR~~~+`pwd`/working-build+g" -e "s+~~~BUILD~~~+devel+g" ssl-admin > ssl-admin.mod
	install -c -m 0755 -S -v ssl-admin.mod working-build/ssl-admin.test

install:

	[ -e "${DESTDIR}/${ETCDIR}/ssl-admin" ] || mkdir -p ${DESTDIR}/${ETCDIR}/ssl-admin
	${SED_CMD} s+~~~ETCDIR~~~+${ETCDIR}+g man1/ssl-admin.1 > ${DESTDIR}/${MANDIR}/man1/ssl-admin.1
	${SED_CMD} s+~~~ETCDIR~~~+${ETCDIR}+g man5/ssl-admin.conf.5 > ${DESTDIR}/${MANDIR}/man5/ssl-admin.conf.5
	install -c -m 0660 -S -v ssl-admin.conf ${DESTDIR}/${ETCDIR}/ssl-admin/ssl-admin.conf.sample
	install -c -m 0660 -S -v openssl.conf ${DESTDIR}/${ETCDIR}/ssl-admin/openssl.conf.sample
	install -c -m 0660 -S -v openssl.conf ${DESTDIR}/${ETCDIR}/ssl-admin/openssl.conf
	${SED_CMD} -e "s+~~~ETCDIR~~~+${ETCDIR}+g" -e "s+~~~BUILD~~~+prod+g" ssl-admin > ssl-admin.mod
	install -c -m 0755 -S -v ssl-admin.mod ${DESTDIR}/${BINDIR}/ssl-admin
	chmod 0444 ${DESTDIR}/${ETCDIR}/ssl-admin/*.conf.sample
