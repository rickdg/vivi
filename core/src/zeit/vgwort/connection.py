# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

import suds
import suds.cache
import suds.client
import threading
import urlparse
import zeit.vgwort.interfaces
import zope.app.appsetup.product
import zope.cachedescriptors.property
import zope.interface


class VGWortWebService(object):
    """This class handles the configuration of URL and authentication
    information, and provides better error handling for errors returned by the
    web service.

    Subclasses should override `service_path` to point to the WSDL file, and
    can then call the service's methods on themselves, e. g. if the web service
    provides a method 'orderPixel', call it as self.orderPixel(args).
    """

    # override in subclass
    service_path = None
    namespace = None

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.lock = threading.Lock()

    @zope.cachedescriptors.property.Lazy
    def client(self):
        client = suds.client.Client(
            self.wsdl,
            username=self.username,
            password=self.password,
            # disable caching of the WSDL file, since it leads to intransparent
            # behaviour when debugging.
            # This means it is downloaded afresh every time, but that doesn't
            # occur often, as the utility is instantiated only once, so it's
            # not performance critical other otherwise bad.
            cache=suds.cache.NoCache())
        return client

    @property
    def wsdl(self):
        return urlparse.urljoin(self.base_url, self.service_path)

    def call(self, method_name, *args, **kw):
        with self.lock:
            try:
                method = getattr(self.client.service, method_name)
                result = method(*args, **kw)
                if isinstance(result, tuple):
                    raise zeit.vgwort.interfaces.TechnicalError(result)
                return result
            except suds.WebFault, e:
                message = str(e.fault.detail[0])
                if hasattr(e.fault.detail, 'ValidationError'):
                    raise TypeError(message)
                elif int(getattr(e.fault.detail[0], 'errorcode', 0)) >= 100:
                    raise zeit.vgwort.interfaces.TechnicalError(message)
                else:
                    raise zeit.vgwort.interfaces.WebServiceError(message)

    def create(self, type_):
        return self.client.factory.create('{%s}%s' % (self.namespace, type_))


class PixelService(VGWortWebService):

    zope.interface.implements(zeit.vgwort.interfaces.IPixelService)

    service_path = '/services/1.0/pixelService.wsdl'
    namespace = 'http://vgwort.de/1.0/PixelService/xsd'

    def order_pixels(self, amount):
        result = self.call('orderPixel', amount)
        for pixel in result.pixels.pixel:
            yield (pixel._publicIdentificationId,
                   pixel._privateIdentificationId)


class MessageService(VGWortWebService):

    zope.interface.implements(zeit.vgwort.interfaces.IMessageService)

    service_path = '/services/1.1/messageService.wsdl'
    namespace = 'http://vgwort.de/1.1/MessageService/xsd'

    def new_document(self, content):
        content = zeit.cms.content.interfaces.ICommonMetadata(content)
        parties = self.create('Parties')
        parties.authors = self.create('Authors')
        for author in content.author_references:
            involved = self.create('Involved')
            involved.firstName = author.firstname
            involved.surName = author.lastname
            involved.cardNumber = author.vgwortid
            parties.authors.author.append(involved)

        if content.product and content.product.vgwortid:
            involved = self.create('Involved')
            involved.firstName = 'n/a' # it's a required field
            involved.surName = content.product.title
            involved.cardNumber = content.product.vgwortid
            parties.authors.author.append(involved)

        text = self.create('MessageText')
        text.text = self.create('Text')
        text._lyric = False
        text.shorttext = content.title
        searchable = zope.index.text.interfaces.ISearchableText(content)
        text.text.plainText = u'\n'.join(
            searchable.getSearchableText()).encode('utf-8').encode('base64')

        ranges = self.create('Webranges')
        url = self.create('Webrange')
        url.url = content.uniqueId.replace(
            'http://xml.zeit.de', 'http://www.zeit.de')
        ranges.webrange.append(url)

        token = zeit.vgwort.interfaces.IToken(content)
        self.call('newMessage', parties, text, ranges,
                  privateidentificationid=token.private_token)


def service_factory(TYPE):
    def factory():
        config = zope.app.appsetup.product.getProductConfiguration(
            'zeit.vgwort')
        return TYPE(config['vgwort-url'],
                    config['username'],
                    config['password'])
    factory = zope.interface.implementer(
        list(zope.interface.implementedBy(TYPE))[0])(factory)
    return factory

real_pixel_service = service_factory(PixelService)
real_message_service = service_factory(MessageService)
