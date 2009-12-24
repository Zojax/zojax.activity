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
from zope import interface
from zope.component.interfaces import IObjectEvent
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('zojax.activity')


class IActivityAware(interface.Interface):
    """ activity aware object """


class IActivity(interface.Interface):
    """ activity configlet """

    records = interface.Attribute('Records')
    catalog = interface.Attribute('Catalog')

    def add(object, record):
        """ add activity record """

    def remove(rid):
        """ remove activity record """

    def removeObject(object):
        """ remove records for object """

    def objectRecords(object):
        """ return object records """

    def updateObjectRecords(object):
        """ reindex records for object """

    def search(**kw):
        """ search records """

    def getObject(id):
        """ return record by id """


class IActivityRecord(interface.Interface):
    """ activity record """

    id = interface.Attribute('Id')
    oid = interface.Attribute('Object Id')
    date = interface.Attribute('Date')
    principal = interface.Attribute('Principal')

    # static info
    type = interface.Attribute('Record type')
    object = interface.Attribute('Content Object')
    description = interface.Attribute('IActivityRecordDescription Object')


class IActivityRecordDescription(interface.Interface):
    """ descriuption object """

    title = interface.Attribute('Title')
    description = interface.Attribute('Description')


class IActivityCatalog(interface.Interface):
    """ activity catalog """


class IActivityRecordEvent(IObjectEvent):
    """ content activity record created event """

    record = interface.Attribute('Activity record')


class IActivityRecordAddedEvent(IActivityRecordEvent):
    """ record added """


class IActivityRecordRemovedEvent(IActivityRecordEvent):
    """ record removed """
