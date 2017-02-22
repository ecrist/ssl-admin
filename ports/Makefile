# Created by: Eric Crist <ecrist@secure-computing.net>
# $FreeBSD: ports/security/ssl-admin/Makefile,v 1.4 2008/07/27 19:05:31 beech Exp $


PORTNAME=	ssl-admin
DISTVERSION=	~~~VERSION~~~
CATEGORIES=	security
MASTER_SITES=	ftp://ftp.secure-computing.net/pub/FreeBSD/ports/ssl-admin/ \
		ftp://ftp2.secure-computing.net/pub/FreeBSD/ports/ssl-admin/

MAINTAINER=	ecrist@secure-computing.net
COMMENT=	OpenSSL certificate manager with OpenVPN support

LICENSE=	BSD3CLAUSE

USES=		perl5 shebangfix
USE_PERL5=	run
RUN_DEPENDS=	zip:${PORTSDIR}/archivers/zip
SUB_FILES=	pkg-message
MAKE_ENV=	ETCDIR=${PREFIX}/etc BINDIR=${PREFIX}/bin \
		MANDIR=${MANPREFIX}/man

.include <bsd.port.mk>
