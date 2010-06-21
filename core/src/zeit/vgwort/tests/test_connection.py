# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

import pkg_resources
import time
import unittest
import zeit.cms.checkout.helper
import zeit.cms.repository.interfaces
import zeit.vgwort.connection
import zeit.vgwort.interfaces
import zeit.vgwort.testing
import zope.component


class WebServiceTest(zeit.vgwort.testing.EndToEndTestCase):

    def setUp(self):
        super(WebServiceTest, self).setUp()
        self.service = zope.component.getUtility(
            zeit.vgwort.interfaces.IMessageService)
        self.repository = zope.component.getUtility(
            zeit.cms.repository.interfaces.IRepository)

    def assertContains(self, needle, haystack):
        if needle not in haystack:
            self.fail(u"%r was not found in %r" % (needle, haystack))

    def add_token(self, content):
        ts = zope.component.getUtility(zeit.vgwort.interfaces.ITokens)
        ts.order(1)
        token = zeit.vgwort.interfaces.IToken(content)
        token.public_token, token.private_token = ts.claim()

    def test_smoketest_successful_call_roundtrip(self):
        result = self.service.call('qualityControl')
        self.assert_(len(result.qualityControlValues) > 0)

    def test_validation_error_should_raise_error_message(self):
        try:
            self.service.new_document(self.repository['testcontent'])
        except TypeError, e:
            self.assertContains(
                "The value 'None' of attribute 'privateidentificationid'",
                str(e))
        else:
            self.fail('TypeError should have been raised.')

    def test_business_fault_should_raise_error_message(self):
        shakespeare = zeit.content.author.author.Author()
        shakespeare.title = 'Sir'
        shakespeare.firstname = 'William'
        shakespeare.lastname = 'Shakespeare'
        shakespeare.vgwortid = 12345
        self.repository['shakespeare'] = shakespeare
        shakespeare = self.repository['shakespeare']

        content = self.repository['testcontent']
        with zeit.cms.checkout.helper.checked_out(content) as co:
            co.author_references = [shakespeare]
            co.title = 'Title'
            co.teaserText = 'asdf'
        content = self.repository['testcontent']
        self.add_token(content)

        try:
            self.service.new_document(content)
        except zeit.vgwort.interfaces.WebServiceError, e:
            self.assertContains('Shakespeare', str(e))
        else:
            self.fail('WebServiceError should have been raised.')

    def test_report_new_document(self):
        author = zeit.content.author.author.Author()
        author.firstname = 'Tina'
        author.lastname = 'Groll'
        author.vgwortid = 2601970
        self.repository['author'] = author
        author = self.repository['author']

        content = self.repository['testcontent']
        with zeit.cms.checkout.helper.checked_out(content) as co:
            co.author_references = [author]
            co.title = 'Title'
            co.teaserText = 'x' * 2000
        content = self.repository['testcontent']
        self.add_token(content)

        self.service.new_document(content)


class RequestHandler(zeit.cms.testing.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        wsdl = pkg_resources.resource_string(__name__, 'pixelService.wsdl')
        wsdl = wsdl.replace('__PORT__', str(port))
        self.wfile.write(wsdl)

    def do_POST(self):
        self.send_response(500)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', 0)
        self.end_headers()
        # suds expects SOAP or nothing (and may the Lord have mercy if the
        # server should return 500 with an HTML error message instead...)
        self.wfile.write('')

HTTPLayer, port = zeit.cms.testing.HTTPServerLayer(RequestHandler)


class HTTPErrorTest(unittest.TestCase):

    layer = HTTPLayer

    def test_http_error_should_raise_technical_error(self):
        service = zeit.vgwort.connection.PixelService(
            'http://localhost:%s' % port, '', '')
        time.sleep(1)
        self.assertRaises(
            zeit.vgwort.interfaces.TechnicalError,
            lambda: list(service.order_pixels(1)))


class MessageServiceTest(zeit.vgwort.testing.TestCase):

    def setUp(self):
        super(MessageServiceTest, self).setUp()
        self.service = zeit.vgwort.connection.real_message_service()
        self.repository = zope.component.getUtility(
            zeit.cms.repository.interfaces.IRepository)

    def test_content_must_have_commonmetadata(self):
        self.assertRaises(
            TypeError, self.service.new_document, None)
