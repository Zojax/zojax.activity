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
from BTrees.IFBTree import IFBTree

from zope import component, interface, event
from zope.proxy import removeAllProxies
from zope.component import getUtility, getAdapter, getAdapters
from zope.app.catalog import catalog
from zope.app.component.hooks import getSite
from zope.app.intid.interfaces import IIntIds
from zope.app.container.interfaces import IObjectAddedEvent
from zope.lifecycleevent import ObjectCreatedEvent
from zc.catalog.catalogindex import SetIndex, ValueIndex

from zojax.catalog.interfaces import ISortable, ICatalogIndexFactory
from zojax.catalog.index import DateTimeValueIndex
from zojax.catalog.result import ResultSet, ReverseResultSet
from zojax.catalog.utils import getAccessList, getRequest, listAllowedRoles

from interfaces import IActivity, IActivityCatalog


class ActivityCatalog(catalog.Catalog):
    interface.implements(IActivityCatalog)

    def createIndex(self, name, factory):
        index = factory()
        event.notify(ObjectCreatedEvent(index))
        self[name] = index

        return self[name]

    def getIndex(self, indexId):
        if indexId in self:
            return self[indexId]

        return self.createIndex(
            indexId, getAdapter(self, ICatalogIndexFactory, indexId))

    def getIndexes(self):
        names = []

        for index in self.values():
            names.append(removeAllProxies(index.__name__))
            yield index

        for name, indexFactory in getAdapters((self,), ICatalogIndexFactory):
            if name not in names:
                yield self.createIndex(name, indexFactory)

    def clear(self):
        for index in self.getIndexes():
            index.clear()

    def index_doc(self, docid, texts):
        for index in self.getIndexes():
            index.index_doc(docid, texts)

    def unindex_doc(self, docid):
        for index in self.getIndexes():
            index.unindex_doc(docid)

    def updateIndexes(self):
        indexes = list(self.getIndexes())

        for uid, obj in self._visitSublocations():
            for index in indexes:
                index.index_doc(uid, obj)

    def _visitSublocations(self):
        configlet = getUtility(IActivity)

        for uid, record in removeAllProxies(configlet).records.items():
            yield uid, record

    def search(self, object=None, contexts=(),
               sort_on='date', sort_order='reverse',
               noSecurityChecks=False, **kw):

        ids = getUtility(IIntIds)

        query = dict(kw)

        # records for object
        if type(object) is not type({}) and object is not None:
            oid = ids.queryId(removeAllProxies(object))
            if oid is None:
                return ResultSet(IFBTree(), getUtility(IActivity))

            query['object'] = {'any_of': (oid,)}

        # context
        if not contexts:
            contexts = (getSite(),)

        c = []
        for context in contexts:
            id = ids.queryId(removeAllProxies(context))
            if id is not None:
                c.append(id)

        query['contexts'] = {'any_of': c}

        # security
        if not noSecurityChecks:
            request = getRequest()
            if request is not None:
                users = listAllowedRoles(request.principal, getSite())
                if 'zope.Anonymous' not in users:
                    users.append('zope.Anonymous')

                query['allowedUsers'] = {'any_of': users}

        # apply searh terms
        results = self.apply(query)
        if results is None:
            results = IFBTree()

        # sort result by index
        if sort_on and sort_on in self:
            sortable = ISortable(self[sort_on], None)
            if sortable is not None:
                results = sortable.sort(results)

        if sort_order == 'reverse':
            return ReverseResultSet(results, getUtility(IActivity))
        else:
            return ResultSet(results, getUtility(IActivity))


@component.adapter(IActivityCatalog, IObjectAddedEvent)
def handleCatalogAdded(catalog, ev):
    list(catalog.getIndexes())

class Factory(object):
    component.adapts(IActivityCatalog)
    interface.implements(ICatalogIndexFactory)

    def __init__(self, catalog):
        self.catalog = catalog

class DateIndex(Factory):
    def __call__(self):
        return DateTimeValueIndex('date', resolution=4)

class TypeIndex(Factory):
    def __call__(self):
        return ValueIndex('type')

class PrincipalIndex(Factory):
    def __call__(self):
        return ValueIndex('principal')

class ObjectIndex(Factory):
    def __call__(self):
        return ValueIndex('value', IndexableObject)

class ContextsIndex(Factory):
    def __call__(self):
        return SetIndex('value', IndexableContexts)

class AllowedUsersIndex(Factory):
    def __call__(self):
        return SetIndex('value', IndexableSecurityInformation)


class IndexableObject(object):

    def __init__(self, record, default=None):
        try:
            self.value = getUtility(IIntIds).getId(
                removeAllProxies(record.object))
        except:
            self.value = default


class IndexableContexts(object):

    def __init__(self, record, default=None):
        values = []
        ids = getUtility(IIntIds)

        context = removeAllProxies(record.object)
        while context is not None:
            values.append(ids.queryId(context))

            context = removeAllProxies(
                getattr(context, '__parent__', None))

        self.value = values


class IndexableSecurityInformation(object):

    def __init__(self, record, default=None):
        self.value = getAccessList(removeAllProxies(record.object), 'zope.View')
