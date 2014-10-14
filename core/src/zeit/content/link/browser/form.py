# Copyright (c) 2007-2011 gocept gmbh & co. kg
# See also LICENSE.txt
"""Link forms."""

from zeit.cms.i18n import MessageFactory as _
import zeit.cms.content.browser.form
import zeit.content.link.interfaces
import zeit.content.link.link
import zeit.push.browser.form
import zope.formlib.form


base = zeit.cms.content.browser.form.CommonMetadataFormBase


class Base(zeit.push.browser.form.SocialBase):

    form_fields = zope.formlib.form.FormFields(
        zeit.content.link.interfaces.ILink).omit(
            'xml', 'authors', 'push_news')

    field_groups = (
        base.field_groups[:3]
        + (zeit.push.browser.form.SocialBase.social_fields,)
        + base.field_groups[3:]
    )


class Add(Base, zeit.cms.content.browser.form.CommonMetadataAddForm):

    title = _('Add link')
    factory = zeit.content.link.link.Link
    form_fields = Base.form_fields.omit(
        'automaticMetadataUpdateDisabled')

    @zope.formlib.form.action(_("Add"),
                              condition=zope.formlib.form.haveInputWidgets)
    def handle_add(self, action, data):
        self.applyAccountData(data)
        return super(Add, self).handle_add.success(data)


class Edit(Base,
           zeit.cms.content.browser.form.CommonMetadataEditForm):

    title = _('Edit link')

    @zope.formlib.form.action(
        _('Apply'), condition=zope.formlib.form.haveInputWidgets)
    def handle_edit_action(self, action, data):
        self.applyAccountData(data)
        return super(Edit, self).handle_edit_action.success(data)


class Display(Base, zeit.cms.content.browser.form.CommonMetadataDisplayForm):

    title = _('View link metadata')
