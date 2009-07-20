# Copyright (c) 2007-2009 gocept gmbh & co. kg
# See also LICENSE.txt

import StringIO
import datetime
import gocept.lxml.objectify
import lxml.objectify
import persistent
import pytz
import rwproperty
import zeit.cms.checkout.interfaces
import zeit.cms.content.interfaces
import zeit.cms.content.lxmlpickle  # extended pickle support
import zeit.cms.interfaces
import zeit.connector.interfaces
import zope.container.contained
import zope.interface
import zope.security.interfaces
import zope.security.proxy


class XMLRepresentationBase(object):

    zope.interface.implements(zeit.cms.content.interfaces.IXMLRepresentation)

    default_template = None  # Define in subclasses

    def __init__(self, xml_source=None):
        if xml_source is None:
            if self.default_template is None:
                raise NotImplementedError(
                    "default_template needs to be set in subclasses")
            xml_source = StringIO.StringIO(self.default_template)
        self.xml = gocept.lxml.objectify.fromfile(xml_source)


class XMLContentBase(XMLRepresentationBase,
                     persistent.Persistent,
                     zope.container.contained.Contained):
    """Base class for xml content."""

    zope.interface.implements(zeit.cms.content.interfaces.IXMLContent)

    uniqueId = None
    __name__ = None

    def __cmp__(self, other):
        if not zeit.cms.interfaces.ICMSContent.providedBy(other):
            return -1
        return cmp(self.__name__, other.__name__)

_default_marker = object()


class Persistent(object):
    """Helper to indicate changes for object modified xml trees."""

    def __setattr__(self, key, value):
        if not key.startswith('_p_'):
            self._p_changed = True
        super(Persistent, self).__setattr__(key, value)

    @rwproperty.getproperty
    def _p_changed(self):
        persistent = self.__get_persistent()
        return persistent._p_changed if persistent is not None else None

    @rwproperty.setproperty
    def _p_changed(self, value):
        persistent = self.__get_persistent()
        if persistent is not None:
           persistent._p_changed = value

    def __get_persistent(self):
        parent = getattr(self, '__parent__', None)
        while parent is not None:
            unproxied = zope.proxy.removeAllProxies(parent)
            if isinstance(unproxied, persistent.Persistent):
                return unproxied
            parent = parent.__parent__


class PropertyToXMLAttribute(object):
    """Attribute nodes reside in the head."""

    zope.component.adapts(zeit.cms.content.interfaces.IXMLRepresentation)
    zope.interface.implements(
        zeit.cms.content.interfaces.IDAVPropertyXMLSynchroniser)

    path = lxml.objectify.ObjectPath('.head.attribute')

    def __init__(self, context):
        self.context = context
        dav_properties = zeit.connector.interfaces.IWebDAVProperties(context)

        # Set the date-last-modified to now
        try:
            dav_properties[('date-last-modified',
                            zeit.cms.interfaces.DOCUMENT_SCHEMA_NS)] = (
                                datetime.datetime.now(pytz.UTC).isoformat())
        except zope.security.interfaces.Forbidden:
            # Don't do this for live properties.
            pass

        self.properties = dict(dav_properties)

        # Now get the current live-properties
        repository = zope.component.queryUtility(
            zeit.cms.repository.interfaces.IRepository)
        if repository and context.uniqueId:
            try:
                repository_content = repository.getContent(context.uniqueId)
            except KeyError:
                pass
            else:
                live_properties = zeit.connector.interfaces.IWebDAVProperties(
                    repository_content)
                self.properties.update(dict(
                    (key, live_properties[key]) for key in live_properties if
                    live_properties.is_live_property(key[0], key[1])))

    def set(self, namespace, name, value=_default_marker):
        self.delAttribute(namespace, name)
        if value is _default_marker:
            value = self.properties[(name, namespace)]
        if value is not zeit.connector.interfaces.DeleteProperty:
            self.addAttribute(namespace, name, value)

    def sync(self):
        # Remove all properties in xml first
        self.path.setattr(self.context.xml, [])

        # Now, set each property to xml, sort them to get a consistent xml
        for ((name, namespace), value) in sorted(self.properties.items()):
            if value is zeit.connector.interfaces.DeleteProperty:
                continue
            self.addAttribute(namespace, name, value)

    def addAttribute(self, namespace, name, value):
        if namespace == 'DAV:':
            # We don't sync DAV: properties.
            return
        root = self.context.xml
        self.path.addattr(root, value)
        node = self.path.find(root)[-1]
        node.set('ns', namespace)
        node.set('name', name)

    def delAttribute(self, namespace, name):
        root = self.context.xml
        xpath = '//head/attribute[@ns="%s" and @name="%s"]' % (
            namespace, name)
        for node in root.findall(xpath):
            parent = node.getparent()
            parent.remove(node)


@zope.component.adapter(
    zeit.cms.content.interfaces.IDAVPropertiesInXML,
    zeit.cms.content.interfaces.IDAVPropertyChangedEvent)
def map_dav_property_to_xml(context, event):
    """Copy dav properties to XML if possible.

    """
    # Remove security proxy: If the user was allowed to change the property
    # (via setattr) *we* copy that to the xml, regardles of the security.
    # XXX shouldn't we check for ILocalContent?
    content = zope.security.proxy.removeSecurityProxy(
        zeit.cms.content.interfaces.IXMLRepresentation(context))
    sync = zeit.cms.content.interfaces.IDAVPropertyXMLSynchroniser(content)
    sync.set(event.property_namespace, event.property_name, event.new_value)


@zope.component.adapter(
    zeit.cms.content.interfaces.IDAVPropertiesInXML,
    zeit.cms.checkout.interfaces.IBeforeCheckinEvent)
def map_dav_properties_to_xml_before_checkin(context, event):
    """Copy over all DAV properties to the xml before checkin.

    """
    content = zope.security.proxy.removeSecurityProxy(
        zeit.cms.content.interfaces.IXMLRepresentation(context))
    sync = zeit.cms.content.interfaces.IDAVPropertyXMLSynchroniser(content)
    sync.sync()


class XMLReferenceUpdater(object):

    zope.component.adapts(zeit.cms.interfaces.ICMSContent)
    zope.interface.implements(
        zeit.cms.content.interfaces.IXMLReferenceUpdater)

    target_iface = None

    def __init__(self, context):
        self.context = context

    def update(self, xml_node):
        """Only run the real update if context is adaptable to target_iface.

        Subclasses need to set the target_iface attribute and implement
        update_with_context(xml_node, context) in order to use this feature.

        """
        context = self.target_iface(self.context, None)
        if context is None:
            return
        return self.update_with_context(xml_node, context)


class XMLReferenceUpdaterRunner(XMLReferenceUpdater):
    """Adapter that updates metadata etc on an XML reference."""

    def update(self, xml_node):
        """Update xml_node with data from the content object."""
        for name, updater in zope.component.getAdapters(
            (self.context,),
            zeit.cms.content.interfaces.IXMLReferenceUpdater):
            if not name:
                # The unnamed adapter is the one which runs all the named
                # adapters, i.e. this one.
                continue
            updater.update(xml_node)


class CommonMetadataUpdater(XMLReferenceUpdater):
    """Put information for ICommonMetadata into the channel."""

    short_title_path = lxml.objectify.ObjectPath('.short.title')
    short_text_path = lxml.objectify.ObjectPath('.short.text')
    homepage_title_path = lxml.objectify.ObjectPath('.homepage.title')
    homepage_text_path = lxml.objectify.ObjectPath('.homepage.text')

    target_iface = zeit.cms.content.interfaces.ICommonMetadata

    def update_with_context(self, entry, metadata):
        entry['supertitle'] = metadata.supertitle
        entry['title'] = metadata.teaserTitle
        entry['text'] = entry['description'] = metadata.teaserText
        entry['byline'] = metadata.byline
        if metadata.year:
            entry.set('year', unicode(metadata.year))
        if metadata.volume:
            entry.set('issue', unicode(metadata.volume))
        self.short_title_path.setattr(entry, metadata.shortTeaserTitle)
        self.short_text_path.setattr(entry, metadata.shortTeaserText)
        self.homepage_title_path.setattr(entry, metadata.hpTeaserTitle)
        self.homepage_text_path.setattr(entry, metadata.hpTeaserText)
