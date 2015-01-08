from zeit.seo.i18n import MessageFactory as _
import zope.interface
import zope.schema


class ISEO(zope.interface.Interface):

    html_title = zope.schema.TextLine(
        title=_('HTML title'),
        required=False)

    html_description = zope.schema.Text(
        title=_('HTML description'),
        required=False)

    meta_robots = zope.schema.Text(
        title=_('Meta robots'),
        required=False)

    hide_timestamp = zope.schema.Bool(
        title=_('Hide timestamp'),
        required=False)
