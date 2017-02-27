# coding: utf-8
import pkg_resources
import zeit.cms.testing
import zeit.content.cp.testing
import zeit.content.image.testing
import zeit.workflow.testing
import plone.testing
import gocept.httpserverlayer.wsgi

import gocept.selenium


product_config = """
<product-config zeit.content.volume>
    volume-cover-source file://{here}/tests/fixtures/volume-covers.xml
    dav-archive-url test
    toc-product-ids ZEI
</product-config>
""".format(here=pkg_resources.resource_filename(__name__, '.'))


ZCML_LAYER = zeit.cms.testing.ZCMLLayer(
    'ftesting.zcml', product_config=(
        product_config +
        zeit.cms.testing.cms_product_config +
        zeit.content.image.testing.product_config +
        zeit.content.cp.testing.product_config +
        zeit.workflow.testing.product_config
    ))


WSGI_LAYER = zeit.cms.testing.WSGILayer(
    name='WSGILayer', bases=(ZCML_LAYER,))
HTTP_LAYER = gocept.httpserverlayer.wsgi.Layer(
    name='HTTPLayer', bases=(WSGI_LAYER,))
WD_LAYER = gocept.selenium.WebdriverLayer(
    name='WebdriverLayer', bases=(HTTP_LAYER,))
WEBDRIVER_LAYER = gocept.selenium.WebdriverSeleneseLayer(
    name='WebdriverSeleneseLayer', bases=(WD_LAYER,))

WORKFLOW_ZCML_LAYER  = plone.testing.Layer(
    name='Layer', module=__name__, bases=(ZCML_LAYER,
                                          zeit.workflow.testing.SCRIPTS_LAYER))


class FunctionalTestCase(zeit.cms.testing.FunctionalTestCase):

    layer = ZCML_LAYER
