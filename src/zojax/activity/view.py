##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id$
"""
from zope.component import getUtility
from zope.proxy import removeAllProxies
from zope.traversing.browser import absoluteURL
from zope.app.component.hooks import getSite
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError

from zojax.batching.batch import Batch
from zojax.formatter.utils import getFormatter
from zojax.statusmessage.interfaces import IStatusMessage

from interfaces import _


class ActivityView(object):

    unknown = _('Unknown')

    def update(self):
        request = self.request
        context = removeAllProxies(self.context)

        if 'form.button.reindex' in request:
            catalog = context.catalog
            catalog.clear()

            for rid, record in context.records.items():
                if record.object is None:
                    context.remove(rid)

            for rid, record in context.records.items():
                catalog.index_doc(rid, record)

            IStatusMessage(request).add(
                _('Activity catalog has been reindexed.'))

        results = context.search(noSecurityChecks=True)

        self.batch = Batch(results, size=20, context=context, request=request)

        self.auth = getUtility(IAuthentication)
        self.formatter = getFormatter(self.request, 'humanDatetime', 'medium')

    def getInfo(self, record):
        info = {'type': record.type,
                'date': self.formatter.format(record.date),
                'object': self.unknown,
                'objectUrl': None,
                'principal': self.unknown}

        object = record.object
        if object is not None:
            info['object'] = getattr(object, 'title', object.__name__)
            try:
                info['objectUrl'] = u'%s/'%absoluteURL(object, self.request)
            except:
                pass

        if record.principal:
            try:
                principal = self.auth.getPrincipal(record.principal)
                info['principal'] = principal.title
            except PrincipalLookupError:
                pass

        return info
