from zeit.wochenende.interfaces import IZWESection, IZWEFolder
import plone.testing
import zeit.cms.testing
import zeit.cms.repository.interfaces
import zeit.content.article.testing
import zope.component


ZCML_LAYER = zeit.cms.testing.ZCMLLayer(bases=(
    zeit.content.article.testing.CONFIG_LAYER,))
ZOPE_LAYER = zeit.cms.testing.ZopeLayer(bases=(ZCML_LAYER,))


class Layer(plone.testing.Layer):

    defaultBases = (ZOPE_LAYER,)

    def testSetUp(self):
        with zeit.cms.testing.site(self['zodbApp']):
            repository = zope.component.getUtility(
                zeit.cms.repository.interfaces.IRepository)
            wochenende = zeit.cms.repository.folder.Folder()
            zope.interface.alsoProvides(wochenende, IZWESection)
            zope.interface.alsoProvides(wochenende, IZWEFolder)
            repository['wochenende'] = wochenende


LAYER = Layer()


class FunctionalTestCase(zeit.cms.testing.FunctionalTestCase):

    layer = LAYER
