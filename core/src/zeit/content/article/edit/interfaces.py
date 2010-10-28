# Copyright (c) 2007-2009 gocept gmbh & co. kg
# See also LICENSE.txt

from zeit.content.article.i18n import MessageFactory as _
import stabledict
import zc.sourcefactory.basic
import zeit.brightcove.interfaces
import zeit.cms.content.field
import zeit.content.gallery.interfaces
import zeit.content.image.interfaces
import zeit.content.infobox.interfaces
import zeit.content.portraitbox.interfaces
import zeit.edit.interfaces
import zope.schema


class IEditableBody(zeit.edit.interfaces.IArea):
    """Editable representation of an article's body."""


class IParagraph(zeit.edit.interfaces.IBlock):
    """<p/> element."""

    text = zope.schema.Text(title=_('Paragraph-Text'))


class IUnorderedList(IParagraph):
    """<ul/> element."""


class IOrderedList(IParagraph):
    """<ol/> element."""


class IIntertitle(IParagraph):
    """<intertitle/> element."""


class IDivision(zeit.edit.interfaces.IBlock):
    """<division/> element"""

    teaser = zope.schema.TextLine(title=_('Page teaser'))


class LayoutSourceBase(zc.sourcefactory.basic.BasicSourceFactory):

    def getValues(self):
        return self.values.keys()

    def getTitle(self, value):
        return self.values[value]


class ImageLayoutSource(LayoutSourceBase):

    values = stabledict.StableDict([
        ('small', _('small')),
        ('large', _('large')),
        ('infobox', _('Infobox')),
        ('upright', _('Hochkant')),
        ])


class IImage(zeit.edit.interfaces.IBlock):

    image = zope.schema.Choice(
        title=_("Image"),
        source=zeit.content.image.interfaces.ImageSource())

    layout = zope.schema.Choice(
        title=_('Layout'),
        source=ImageLayoutSource(),
        required=False)


class VideoLayoutSource(LayoutSourceBase):

    values = stabledict.StableDict([
        (u'small', _('small')),
        (u'with-links', _('with info')),
        (u'large',  _('large')),
        (u'double', _('double')),
    ])


class IVideo(zeit.edit.interfaces.IBlock):

    video = zope.schema.Choice(
        title=_('Video'),
        required=False,
        source=zeit.brightcove.interfaces.brightcoveSource)

    video_2 = zope.schema.Choice(
        title=_('Video 2'),
        required=False,
        source=zeit.brightcove.interfaces.brightcoveSource)

    layout = zope.schema.Choice(
        title=_('Layout'),
        source=VideoLayoutSource(),
        required=False)


class IReference(zeit.edit.interfaces.IBlock):
    """A block which references another object."""

    references = zope.schema.Field(title=_('Referenced object.'))


class IGallery(IReference):
    """block for <gallery/> tags."""

    references = zope.schema.Choice(
        title=_('Gallery'),
        source=zeit.content.gallery.interfaces.gallerySource)


class IInfobox(IReference):
    """block for <infobox/> tags."""

    references = zope.schema.Choice(
        title=_('Infobox'),
        source=zeit.content.infobox.interfaces.infoboxSource)


class PortraitboxLayoutSource(LayoutSourceBase):

    values = stabledict.StableDict([
        (u'short', _('short')),
        (u'wide', _('wide')),
    ])


class IPortraitbox(IReference):
    """block for <infobox/> tags."""

    references = zope.schema.Choice(
        title=_('Portraitbox'),
        source=zeit.content.portraitbox.interfaces.portraitboxSource)

    layout = zope.schema.Choice(
        title=_('Layout'),
        source=PortraitboxLayoutSource(),
        required=False)


class ValidationError(zope.schema.ValidationError):

    def doc(self):
        return self.args[0]


def validate_rawxml(xml):
    if xml.tag != 'raw':
        raise ValidationError(_("The root element must be <raw>."))
    return True


class IRawXML(zeit.edit.interfaces.IBlock):

    xml = zeit.cms.content.field.XMLTree(
        title=_('XML source'),
        constraint=validate_rawxml)


class IAudio(zeit.edit.interfaces.IBlock):

    audio_id = zope.schema.TextLine(
        title=_('Audio id'))

    expires = zope.schema.Datetime(
        title=_('Expires'),
        required=False)
