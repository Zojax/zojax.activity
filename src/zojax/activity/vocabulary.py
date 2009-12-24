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
from zope.component import getUtilitiesFor
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.schema.interfaces import IVocabulary, IVocabularyFactory

from interfaces import IActivityRecordDescription


@interface.implementer(IVocabularyFactory)
def ActivityRecordDescriptions(context):
    terms = []
    for name, desc in getUtilitiesFor(IActivityRecordDescription):
        term = SimpleTerm(name, name, desc.title)
        term.description = desc.description
        terms.append((desc.title, name, term))

    terms.sort()
    return SimpleVocabulary([term for t, n, term in terms])
