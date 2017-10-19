from __future__ import absolute_import
import gocept.httpserverlayer.custom
import json
import mock
import pkg_resources
import plone.testing
import zeit.cms.content.interfaces
import zeit.cms.testcontenttype.testcontenttype
import zeit.cms.testing
import zeit.content.article.testing
import zeit.content.image.testing
import zeit.content.volume.testing
import zeit.workflow.testing


class RequestHandler(gocept.httpserverlayer.custom.RequestHandler):

    def do_GET(self):
        length = int(self.headers.get('content-length', 0))
        self.requests.append(dict(
            verb=self.command,
            path=self.path,
            body=self.rfile.read(length) if length else None,
        ))
        self.send_response(self.response_code)
        self.end_headers()
        self.wfile.write(self.response_body)

    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET


class HTTPLayer(gocept.httpserverlayer.custom.Layer):

    def testSetUp(self):
        super(HTTPLayer, self).testSetUp()
        self['request_handler'].requests = []
        self['request_handler'].response_body = '{}'
        self['request_handler'].response_code = 200

HTTP_LAYER = HTTPLayer(RequestHandler, name='HTTPLayer', module=__name__)


product_config = """
<product-config zeit.retresco>
    base-url http://localhost:[PORT]
    elasticsearch-url http://tms-backend.staging.zeit.de:80/elasticsearch
    elasticsearch-index zeit_pool
    topic-redirect-prefix http://www.zeit.de
</product-config>
"""


class ElasticsearchMockLayer(plone.testing.Layer):

    def setUp(self):
        self['elasticsearch_mocker'] = mock.patch(
            'elasticsearch.client.Elasticsearch.search')
        self['elasticsearch'] = self['elasticsearch_mocker'].start()
        filename = pkg_resources.resource_filename(
            'zeit.retresco.tests', 'elasticsearch_result.json')
        with open(filename) as response:
            self['elasticsearch'].return_value = json.load(response)

    def tearDown(self):
        del self['elasticsearch']
        self['elasticsearch_mocker'].stop()
        del self['elasticsearch_mocker']


ELASTICSEARCH_MOCK_LAYER = ElasticsearchMockLayer()


class ZCMLLayer(zeit.cms.testing.ZCMLLayer):

    defaultBases = zeit.cms.testing.ZCMLLayer.defaultBases + (HTTP_LAYER,)

    def setUp(self):
        self.product_config = self.product_config.replace(
            '[PORT]', str(self['http_port']))
        super(ZCMLLayer, self).setUp()


ZCML_LAYER = ZCMLLayer(
    'ftesting.zcml', product_config=zeit.cms.testing.cms_product_config +
    product_config +
    zeit.workflow.testing.product_config +
    zeit.content.article.testing.product_config +
    zeit.content.volume.testing.product_config +
    zeit.content.image.testing.product_config)


MOCK_ZCML_LAYER = plone.testing.Layer(
    bases=(ZCML_LAYER, ELASTICSEARCH_MOCK_LAYER), name='MockZCMLLayer',
    module=__name__)


class FunctionalTestCase(zeit.cms.testing.FunctionalTestCase):

    layer = ZCML_LAYER


class TagTestHelpers(object):
    """Helper to prefill DAV-Property used for keywords of a content object."""

    def set_tags(self, content, xml):
        """Prefill DAV-Property for keywords of `content` with `xml`.

        It inserts `xml` into a newly created DAV-property 'rankedTags' under
        the tagging-namespace key. `xml` is a string containing XML
        representing `Tag` objects, which requires `type` and `text`::

            <tag type="Person">Karen Duve</tag>
            <tag type="Location">Berlin</tag>

        """

        dav = zeit.connector.interfaces.IWebDAVProperties(content)
        name, ns = dav_key = (
            'rankedTags', 'http://namespaces.zeit.de/CMS/tagging')
        dav[dav_key] = """<ns:{tag} xmlns:ns="{ns}">
        <rankedTags>{0}</rankedTags></ns:{tag}>""".format(
            xml, ns=ns, tag=name)


def create_testcontent():
    content = zeit.cms.testcontenttype.testcontenttype.ExampleContentType()
    content.uniqueId = 'http://xml.zeit.de/testcontent'
    content.teaserText = 'teaser'
    content.title = 'title'
    zeit.cms.content.interfaces.IUUID(content).id = 'myid'
    return content