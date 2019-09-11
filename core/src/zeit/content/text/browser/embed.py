from zeit.cms.content.sources import FEATURE_TOGGLES
from zeit.cms.i18n import MessageFactory as _
import zeit.cmp.interfaces
import zeit.cms.browser.form
import zeit.content.text.embed
import zeit.content.text.interfaces
import zope.formlib.form


class FormBase(object):

    form_fields = zope.formlib.form.FormFields(
        zeit.content.text.interfaces.IEmbed).select('__name__', 'text')


class Add(FormBase, zeit.cms.browser.form.AddForm):

    title = _('Add embed')
    factory = zeit.content.text.embed.Embed


class Edit(FormBase, zeit.cms.browser.form.EditForm):

    title = _('Edit embed')


class Parameters(FormBase, zeit.cms.browser.form.EditForm):

    title = _('Edit embed parameters')
    form_fields = zope.formlib.form.FormFields(
        zeit.content.text.interfaces.IEmbed,
        zeit.cms.content.interfaces.IMemo).select(
            'render_as_template', 'parameter_definition', 'vivi_css', 'memo')

    def __init__(self, context, request):
        super(FormBase, self).__init__(context, request)
        if FEATURE_TOGGLES.find('embed_cmp_thirdparty'):
            self.form_fields += zope.formlib.form.FormFields(
                zeit.cmp.interfaces.IConsentInfo).select(
                    'has_thirdparty', 'thirdparty_vendors')


class Display(zeit.cms.browser.form.DisplayForm):

    title = _('View embed')
    form_fields = zope.formlib.form.FormFields(
        zeit.content.text.interfaces.IEmbed,
        zeit.cms.content.interfaces.IMemo,
        zeit.cmp.interfaces.IConsentInfo)
