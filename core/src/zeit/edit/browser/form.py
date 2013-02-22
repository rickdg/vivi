# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

from zeit.cms.i18n import MessageFactory as _
import json
import zeit.cms.browser.form
import zeit.cms.browser.view
import zeit.cms.checkout.interfaces
import zeit.edit.browser.view
import zope.app.pagetemplate
import zope.formlib.form
import zope.formlib.interfaces
import zope.formlib.itemswidgets
import zope.formlib.source
import zope.formlib.widget


class Forms(object):
    """View that collects all inline forms."""


FormGroup = zope.viewlet.viewlet.SimpleViewletClass('layout.forms.pt')


class FoldableFormGroup(zope.viewlet.viewlet.SimpleViewletClass(
        'layout.foldable-forms.pt')):

    folded_workingcopy = True
    folded_repository = True

    @property
    def folded(self):
        if zeit.cms.checkout.interfaces.ILocalContent.providedBy(self.context):
            return self.folded_workingcopy
        else:
            return self.folded_repository


FormLoader = zope.viewlet.viewlet.SimpleViewletClass('layout.form-loader.pt')


class InlineForm(zeit.cms.browser.form.WidgetCSSMixin,
                 zeit.cms.browser.form.PlaceholderMixin,
                 zope.formlib.form.SubPageEditForm,
                 zeit.edit.browser.view.UndoableMixin,
                 zeit.cms.browser.view.Base):

    template = zope.app.pagetemplate.ViewPageTemplateFile('inlineform.pt')

    css_class = None

    def __init__(self, *args, **kw):
        super(InlineForm, self).__init__(*args, **kw)
        self._signals = []

    def signal(self, name, *args):
        self._signals.append(dict(name=name, args=args))

    @property
    def signals(self):
        return json.dumps(self._signals)

    @zope.formlib.form.action(_('Apply'), failure='success_handler')
    def handle_edit_action(self, action, data):
        return self.success_handler(action, data)

    def success_handler(self, action, data, errors=None):
        self.mark_transaction_undoable()
        self._success_handler()
        return super(InlineForm, self).handle_edit_action.success(data)

    def _success_handler(self):
        pass

    def validate(self, action, data):
        errors = super(InlineForm, self).validate(action, data)
        self.get_all_input_even_if_invalid(data)
        return errors

    def get_all_input_even_if_invalid(self, data):
        form_prefix = zope.formlib.form.expandPrefix(self.prefix)
        for input, widget in self.widgets.__iter_input_and_widget__():
            if input and zope.formlib.interfaces.IInputWidget.providedBy(
                widget):
                name = zope.formlib.form._widgetKey(widget, form_prefix)
                try:
                    try:
                        # combination widget has a helper for us.
                        data[name] = widget.loadValueFromRequest()
                    except AttributeError:
                        data[name] = widget._toFieldValue(
                            widget._getFormInput())
                except zope.formlib.interfaces.ConversionError:
                    pass

    def is_basic_display_widget(self, widget):
        # XXX kludgy. We want to express "is this a base widget out of
        # zope.formlib?" (since those are the ones we want to style differently
        # in readonly-mode).
        # We can't use IDisplayWidget, since a) some formlib
        # widgets don't provide it while b) some widgets we don't want to
        # include (like ObjectSequenceDisplayWidget) do provide it.
        return type(widget) in [
            zope.formlib.widget.DisplayWidget,
            zope.formlib.widget.UnicodeDisplayWidget,
            zope.formlib.source.SourceDisplayWidget,
            zope.formlib.itemswidgets.ItemDisplayWidget,
        ]
