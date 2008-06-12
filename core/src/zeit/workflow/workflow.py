# Copyright (c) 2007-2008 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$

import UserDict
import datetime
import logging

import pytz

import zope.component
import zope.event
import zope.interface
import zope.location.location

import z3c.flashmessage.interfaces

import zeit.objectlog.interfaces

import zeit.cms.interfaces
import zeit.cms.content.dav
import zeit.cms.content.interfaces
import zeit.cms.checkout.interfaces
import zeit.cms.relation.interfaces
import zeit.cms.workflow.interfaces
from zeit.cms.i18n import MessageFactory as _

import zeit.workflow.interfaces
import zeit.workflow.timebased


if 'all' not in globals():
    # Python 2.4 doesn't have `all` :(
    def all(iterable):
        for element in iterable:
            if not element:
                return False
        return True


WORKFLOW_NS = zeit.workflow.interfaces.WORKFLOW_NS
logger = logging.getLogger(__name__)


class ContentWorkflow(zeit.workflow.timebased.TimeBasedWorkflow):
    """Adapt ICMSContent to IWorkflow using the "live" data from connector.

    We must read and write properties directly from the DAV to be sure we
    actually can do the transition.
    """

    zope.interface.implements(zeit.workflow.interfaces.IContentWorkflow)
    zope.component.adapts(zeit.cms.interfaces.ICMSContent)

    zeit.cms.content.dav.mapProperties(
        zeit.workflow.interfaces.IContentWorkflow,
        WORKFLOW_NS,
        ('edited', 'corrected', 'refined', 'images_added', 'urgent'),
        live=True)

    def can_publish(self):
        if self.urgent:
            return True
        if all([self.edited, self.corrected, self.refined, self.images_added]):
            return True
        return False



class FeedMetadataUpdater(object):
    """Add the expire/publication time to feed entry."""

    zope.interface.implements(
        zeit.cms.syndication.interfaces.IFeedMetadataUpdater)

    def update_entry(self, entry, content):
        workflow = zeit.workflow.interfaces.IContentWorkflow(content, None)
        if workflow is None:
            return

        date = ''
        if workflow.released_from:
            date = workflow.released_from.isoformat()
        entry.set('publication-date', date)

        date = ''
        if workflow.released_to:
            date = workflow.released_to.isoformat()
        entry.set('expires', date)


@zope.component.adapter(
    zeit.workflow.interfaces.IContentWorkflow,
    zeit.cms.content.interfaces.IDAVPropertyChangedEvent)
def log_workflow_changes(workflow, event):
    if event.field.__name__ not in ('edited', 'corrected', 'refined',
                                    'images_added', 'urgent'):
        # Only act on certain fields.
        return

    content = workflow.context
    message = _('${name}: ${new_value}',
                mapping=dict(name=event.field.title,
                             old_value=event.old_value,
                             new_value=event.new_value))

    log = zope.component.getUtility(zeit.objectlog.interfaces.IObjectLog)
    log.log(content, message)


@zope.component.adapter(
    zeit.cms.interfaces.ICMSContent,
    zeit.cms.workflow.interfaces.IRetractedEvent)
def remove_from_channels_after_retract(context, event):
    """Removes objects from channels when they're retracted."""
    relations = zope.component.getUtility(
        zeit.cms.relation.interfaces.IRelations)
    syndicated_in = relations.get_relations(context, 'syndicated_in')
    for feed in syndicated_in:
        manager = zeit.cms.checkout.interfaces.ICheckoutManager(feed)
        try:
            checked_out = manager.checkout()
        except zeit.cms.checkout.interfaces.CheckinCheckoutError:
            logger.error(
                "Could not remove %s from %s because channel locked." % (
                    context.uniqueId, feed.uniqueId))
            continue
        try:
            checked_out.remove(context)
        except ValueError:
            # Was not in the feed, i.e. the index wasn't up to date. Ignore.
            pass
        manager = zeit.cms.checkout.interfaces.ICheckinManager(checked_out)
        manager.checkin()
