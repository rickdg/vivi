import zeit.cms.content.dav
import zeit.cms.content.interfaces
import zeit.cms.interfaces
import zope.interface


@zope.interface.implementer(
    zeit.cms.content.interfaces.ICachingTime)
class CachingTime(zeit.cms.content.dav.DAVPropertiesAdapter):

    browser = zeit.cms.content.dav.DAVProperty(
        zeit.cms.content.interfaces.ICachingTime['browser'],
        zeit.cms.interfaces.ZEITWEB_NAMESPACE,
        'browser')
    server = zeit.cms.content.dav.DAVProperty(
        zeit.cms.content.interfaces.ICachingTime['server'],
        zeit.cms.interfaces.ZEITWEB_NAMESPACE,
        'server')
