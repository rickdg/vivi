# Copyright (c) 2007-2008 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$

import zope.component
import zope.interface

import zeit.cms.content.dav
import zeit.cms.content.interfaces
import zeit.cms.content.keyword
import zeit.cms.content.property
import zeit.cms.content.xmlsupport


class CommonMetadata(zeit.cms.content.xmlsupport.XMLContentBase):

    zope.interface.implements(
        zeit.cms.content.interfaces.ICommonMetadata)

    zeit.cms.content.dav.mapProperties(
        zeit.cms.content.interfaces.ICommonMetadata,
        zeit.cms.interfaces.DOCUMENT_SCHEMA_NS,
        ('serie', 'copyrights', 'year', 'volume', 'ressort', 'page',
         'sub_ressort', 'vg_wort_id'))

    authors = zeit.cms.content.dav.DAVProperty(
        zeit.cms.content.interfaces.ICommonMetadata['authors'],
        zeit.cms.interfaces.DOCUMENT_SCHEMA_NS,
        'author',
        use_default=True)

    keywords = zeit.cms.content.keyword.KeywordsProperty()

    title = zeit.cms.content.property.Structure(
        '.body.title')
    subtitle = zeit.cms.content.property.Structure(
        '.body.subtitle')
    supertitle = zeit.cms.content.property.ObjectPathProperty(
        '.body.supertitle')
    byline = zeit.cms.content.property.ObjectPathProperty(
        '.body.byline')

    teaserTitle = zeit.cms.content.property.ObjectPathProperty(
        '.teaser.title')
    teaserText = zeit.cms.content.property.ObjectPathProperty(
        '.teaser.text')

    shortTeaserTitle = zeit.cms.content.property.ObjectPathProperty(
        '.indexteaser.title')
    shortTeaserText = zeit.cms.content.property.ObjectPathProperty(
        '.indexteaser.text')

    hpTeaserTitle = zeit.cms.content.property.ObjectPathProperty(
        '.homepageteaser.title')
    hpTeaserText = zeit.cms.content.property.ObjectPathProperty(
        '.homepageteaser.text')
