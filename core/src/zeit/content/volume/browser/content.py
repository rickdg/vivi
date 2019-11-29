import zope.app.locking.interfaces
import zope.app.security.interfaces
import zope.component
import zope.interface
import zope.interface.common.idatetime
import zope.viewlet.interfaces
from zeit.workflow.interfaces import IContentWorkflow
from zeit.content.image.interfaces import IImages
import zeit.cms.browser.listing
import zeit.cms.browser.interfaces
import zeit.cms.content.sources
import zeit.cms.interfaces
import zeit.content.volume.browser.interfaces
from zeit.cms.i18n import MessageFactory as _

import zc.table.column
import zc.table.table

class CheckColumn(zeit.cms.browser.listing.GetterColumn):

    def cell_formatter(self, value, item, formatter):
        if value:
            return '&#10004;'
        else:
            return ''


class ContentListing(zeit.cms.browser.listing.Listing):

    teaser_image_available = _('Teaser image available')
    supertitle_available = _('Supertitle available')
    contenttype = _('Content-Typ')
    availability = _('Availability')
    is_urgent = _('is urgent')
    is_seo_optimized = _('is SEO optimized')
    ressort = _('Ressort')
    rows = _('rows')

    css_class = 'contentListing hasMetadata content_listing'

    columns = (
        zeit.cms.browser.listing.Listing.columns[0:5] +
        (zeit.cms.browser.listing.GetterColumn(
            _('Supertitle'),
            name='supertitle',
            getter=lambda t, c: t.supertitle),) +
        zeit.cms.browser.listing.Listing.columns[5:6] +
        (zeit.cms.browser.listing.GetterColumn(
            _('Ressort'),
            name='ressort',
            getter=lambda t, c: t.printRessort),) +
        zeit.cms.browser.listing.Listing.columns[8:9] +
        (CheckColumn(
                _('Urgent'),
                name='urgent',
                getter=lambda t, c: t.workflow.urgent),
            CheckColumn(
                _('status-seo-optimized'),
                name='seo-optimized',
                getter=lambda t, c: t.workflow.seo_optimized),) +
        zeit.cms.browser.listing.Listing.columns[8:10] +
        (CheckColumn(
            _('Teaserimage'),
            name='teaserimage',
            getter=lambda t, c: t.teaserimage is not None),) +
        zeit.cms.browser.listing.Listing.columns[10:]
    )


class ContentListRepresentation(object):

    @zope.cachedescriptors.property.Lazy
    def ressort(self):
        if self.context.printRessort:
            return self.context.printRessort
        return self.context.ressort

    @zope.cachedescriptors.property.Lazy
    def urgent(self):
        if IContentWorkflow(self.context).urgent:
            return True
        return False

    @zope.cachedescriptors.property.Lazy
    def seo_optimized(self):
        if IContentWorkflow(self.context).seo_optimized:
            return True
        return False

    @zope.cachedescriptors.property.Lazy
    def teaserimage(self):
        if IImages(self.context).image is not None:
            return True
        return False
