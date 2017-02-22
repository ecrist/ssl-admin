# Ports collection makefile for:	ssl-admin
# Date created:				Thu Jan 14 10:38:23 CST 2010
# Whom:					Eric Crist <ecrist@secure-computing.net>
#
# $FreeBSD: ports/security/ssl-admin/Makefile,v 1.4 2008/07/27 19:05:31 beech Exp $
#

PORTNAME=	ssl-admin
DISTVERSION=	1.0.3
CATEGORIES=	security
MASTER_SITES=	ftp://ftp.secure-computing.net/pub/FreeBSD/ports/ssl-admin/

MAINTAINER=	ecrist@secure-computing.net
COMMENT=	OpenSSL certificate manager with OpenVPN support.

RUN_DEPENDS=	unzip:${PORTSDIR}/archivers/unzip \
		zip:${PORTSDIR}/archivers/zip

USE_PERL5_RUN=	YES
MAN1=		ssl-admin.1
MAN5=		ssl-admin.conf.5
SUB_FILES=	pkg-message

post-install:
	${CAT} ${PKGMESSAGE}

.include <bsd.port.mk>
