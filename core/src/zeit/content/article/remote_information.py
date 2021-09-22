import zope.interface

import zeit.cms.content.dav
import zeit.cms.interfaces
import zeit.content.article.interfaces


@zope.interface.implementer(
    zeit.content.article.interfaces.IRemoteInformation)
class RemoteInformaton(zeit.cms.content.dav.DAVPropertiesAdapter):

    zeit.cms.content.dav.mapProperties(
        zeit.content.article.interfaces.IRemoteInformation,
        zeit.cms.interfaces.ZEITWEB_NAMESPACE,
        ('remote_image', 'remote_timestamp'))
