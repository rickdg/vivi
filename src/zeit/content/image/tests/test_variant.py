from zeit.cms.checkout.helper import checked_out
from zeit.content.image.interfaces import IVariants
import zeit.cms.testing
import zeit.content.image.testing
import zope.interface.verify


class VariantTraversal(zeit.cms.testing.FunctionalTestCase):

    layer = zeit.content.image.testing.ZCML_LAYER

    def setUp(self):
        super(VariantTraversal, self).setUp()
        self.group = zeit.content.image.testing.create_image_group()

    def test_variants_provides_mapping_interface(self):
        zope.interface.verify.verifyObject(IVariants, IVariants(self.group))

    def test_access_variants_dict_entries_as_objects(self):
        with checked_out(self.group) as co:
            co.variants = {
                'square': {'focus_x': 0.1, 'focus_y': 0.1, 'zoom': 0.3}
            }
            variant = IVariants(co)['square']
            self.assertEqual(0.1, variant.focus_x)
            self.assertEqual(0.1, variant.focus_y)
            self.assertEqual(0.3, variant.zoom)

    def test_variant_without_settings_returns_default_settings(self):
        with checked_out(self.group) as co:
            co.variants = {
                'default': {'focus_x': 0.1, 'focus_y': 0.1, 'zoom': 0.5}
            }
            variant = IVariants(co)['square']
            self.assertEqual(0.1, variant.focus_x)
            self.assertEqual(0.1, variant.focus_y)
            self.assertEqual(0.5, variant.zoom)

    def test_variant_without_settings_without_default_returns_config(self):
        variant = IVariants(self.group)['square']
        self.assertEqual(0.5, variant.focus_x)
        self.assertEqual(0.5, variant.focus_y)
        self.assertEqual(1, variant.zoom)