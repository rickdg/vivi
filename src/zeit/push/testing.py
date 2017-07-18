import pkg_resources
import plone.testing
import gocept.selenium
import logging
import zeit.cms.repository.interfaces
import zeit.cms.testing
import zeit.content.article.testing
import zeit.push.interfaces
import zeit.workflow.testing
import zope.interface
import zeit.content.text.text


log = logging.getLogger(__name__)


class PushNotifier(object):

    zope.interface.implements(zeit.push.interfaces.IPushNotifier)

    def __init__(self):
        self.reset()

    def reset(self):
        self.calls = []

    def send(self, text, link, **kw):
        self.calls.append((text, link, kw))
        log.info('PushNotifier.send(%s)', dict(
            text=text, link=link, kw=kw))

BASE_ZCML_LAYER = zeit.cms.testing.ZCMLLayer('testing.zcml', product_config=(
    zeit.push.product_config +
    zeit.cms.testing.cms_product_config +
    zeit.workflow.testing.product_config +
    zeit.content.article.testing.product_config))


class PushMockLayer(plone.testing.Layer):
    """Helper layer to reset mock notifiers."""

    def testSetUp(self):
        for service in ['urbanairship', 'twitter', 'facebook', 'homepage']:
            notifier = zope.component.getUtility(
                zeit.push.interfaces.IPushNotifier, name=service)
            notifier.reset()

PUSH_MOCK_LAYER = PushMockLayer()


class UrbanairshipTemplateLayer(plone.testing.Layer):

    defaultBases = (BASE_ZCML_LAYER, )

    def testSetUp(self):
        # Add a dummy template
        with zeit.cms.testing.site(self['functional_setup'].getRootFolder()):
            with zeit.cms.testing.interaction():
                zeit.cms.content.add.find_or_create_folder('data',
                                                           'payload-templates')
                repository = zope.component.getUtility(
                    zeit.cms.repository.interfaces.IRepository)
                textcontent = zeit.content.text.text.Text()
                textcontent.text = ''
                repository['data']['payload-templates']['foo.json'] = \
                    textcontent


URBANAIRSHIP_TEMPLATE_LAYER = UrbanairshipTemplateLayer()

ZCML_LAYER = plone.testing.Layer(
    bases=(URBANAIRSHIP_TEMPLATE_LAYER, PUSH_MOCK_LAYER),
    name='ZCMLPushMockLayer',
    module=__name__)


class TestCase(zeit.cms.testing.FunctionalTestCase):

    layer = ZCML_LAYER

    def create_test_payload_template(self,
                                     template_text=None,
                                     template_name='template.json'):
        with zeit.cms.testing.site(self.getRootFolder()):
            with zeit.cms.testing.interaction():
                zeit.cms.content.add.find_or_create_folder('data',
                                                           'payload-templates')
                template = zeit.content.text.text.Text()
                if not template_text:
                    filename = "{fixtures}/payloadtemplate.json".format(
                        fixtures=pkg_resources.resource_filename(
                            __name__, 'tests/fixtures'))
                    with open(filename) as jsonfile:
                        template.text = jsonfile.read()
                else:
                    template.text = template_text
                self.repository['data']['payload-templates'][template_name]\
                    = template


WSGI_LAYER = zeit.cms.testing.WSGILayer(
    name='WSGILayer', bases=(ZCML_LAYER,))
HTTP_LAYER = gocept.httpserverlayer.wsgi.Layer(
    name='HTTPLayer', bases=(WSGI_LAYER,))
WD_LAYER = gocept.selenium.WebdriverLayer(
    name='WebdriverLayer', bases=(HTTP_LAYER,))
WEBDRIVER_LAYER = gocept.selenium.WebdriverSeleneseLayer(
    name='WebdriverSeleneseLayer', bases=(WD_LAYER,))
