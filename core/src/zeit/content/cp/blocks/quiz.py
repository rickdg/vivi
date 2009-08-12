# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt

from zeit.content.cp.blocks.teaser import create_xi_include
from zeit.content.cp.i18n import MessageFactory as _
import zeit.cms.content.property
import zeit.cms.content.xmlsupport
import zeit.cms.content.xmlsupport
import zeit.content.cp.blocks.block
import zeit.content.cp.interfaces
import zeit.content.quiz.interfaces
import zope.component
import zope.interface


class QuizBlock(zeit.content.cp.blocks.block.Block):

    zope.interface.implements(zeit.content.cp.interfaces.IQuizBlock)

    referenced_quiz = zeit.cms.content.property.SingleResource(
        '.block', xml_reference_name='quizblock', attributes=('href',))


QuizBlockFactory = zeit.content.cp.blocks.block.elementFactoryFactory(
    zeit.content.cp.interfaces.IRegion, 'quiz', _('Quizblock'))


@zope.component.adapter(zeit.content.quiz.interfaces.IQuiz)
@zope.interface.implementer(zeit.cms.content.interfaces.IXMLReference)
def quiz_xi_include(context):
    node = zope.component.getAdapter(
        context, zeit.cms.content.interfaces.IXMLReference, name='related')
    node.append(create_xi_include(context, '/quiz/question'))
    return node
