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
import random
import BTrees

from zope import interface, event, component
from zope.component import getUtility
from zope.proxy import removeAllProxies
from zope.app.intid.interfaces import IIntIds, IIntIdRemovedEvent

from catalog import ActivityCatalog
from interfaces import IActivity, IActivityAware
from interfaces import IActivityRecordAddedEvent
from interfaces import IActivityRecordRemovedEvent


class ActivityConfiglet(object):
    interface.implements(IActivity)

    family = BTrees.family32

    _v_nextid = None
    _randrange = random.randrange

    @property
    def records(self):
        data = self.data.get('records')
        if data is None:
            data = self.family.IO.BTree()
            self.data['records'] = data
        return data

    @property
    def catalog(self):
        catalog = self.data.get('catalog')
        if catalog is None:
            catalog = ActivityCatalog()
            self.data['catalog'] = catalog
        return catalog

    def _generateId(self):
        records = self.records

        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(0, self.family.maxint)

            id = self._v_nextid
            self._v_nextid += 1

            if id not in records:
                return id

            self._v_nextid = None

    def search(self, **kw):
        return self.catalog.search(**kw)

    def objectRecords(self, object):
        return self.catalog.search(object=object, noSecurityChecks=True)

    def updateObjectRecords(self, object):
        catalog = self.catalog

        for record in catalog.search(object=object, noSecurityChecks=True):
            catalog.index_doc(record.id, record)

    def getObject(self, id):
        return self.records[id]

    def add(self, object, record):
        if not IActivityAware.providedBy(object):
            return

        oid = getUtility(IIntIds).queryId(removeAllProxies(object))
        if oid is None:
            return

        record.id = self._generateId()
        record.oid = oid

        self.records[record.id] = record
        self.catalog.index_doc(record.id, record)

        event.notify(ActivityRecordAddedEvent(object, record))

    def remove(self, rid):
        records = self.records

        record = records[rid]
        event.notify(ActivityRecordRemovedEvent(record.object, record))
        self.catalog.unindex_doc(rid)
        del records[rid]

    def removeObject(self, object):
        records = self.records
        catalog = self.catalog

        for rid in self.catalog.search(object, noSecurityChecks=True).uids:
            event.notify(ActivityRecordRemovedEvent(object, records[rid]))

            self.catalog.unindex_doc(rid)
            del records[rid]


class ActivityRecordEvent(object):

    def __init__(self, object, record):
        self.object = object
        self.record = record


class ActivityRecordAddedEvent(ActivityRecordEvent):
    interface.implements(IActivityRecordAddedEvent)


class ActivityRecordRemovedEvent(ActivityRecordEvent):
    interface.implements(IActivityRecordRemovedEvent)


@component.adapter(IActivityAware, IIntIdRemovedEvent)
def objectRemovedHandler(object, ev):
    removeAllProxies(getUtility(IActivity)).removeObject(object)
