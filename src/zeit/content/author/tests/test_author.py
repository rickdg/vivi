import mock
import pysolr
import unittest
import zeit.content.author.author


NONZERO = 3


class AuthorTest(unittest.TestCase):

    def test_author_exists(self):
        author = zeit.content.author.author.Author()
        author.firstname = u'William'
        author.lastname = u'Shakespeare'
        with mock.patch('zeit.find.search.query', lambda **kw: kw):
            with mock.patch('zeit.find.search.search') as search:
                search.return_value = pysolr.Results(None, hits=0)
                self.assertFalse(author.exists)
                search.assert_called_with(dict(
                    fulltext=u'William Shakespeare', types=('author',)))

                search.return_value = pysolr.Results(None, hits=NONZERO)
                self.assertTrue(author.exists)
                search.assert_called_with(dict(
                    fulltext=u'William Shakespeare', types=('author',)))


class ModifiedHandlerTest(unittest.TestCase):

    def test_authorships_should_be_copied_to_freetext(self):
        from zope.lifecycleevent import ObjectModifiedEvent, Attributes
        from zeit.cms.content.interfaces import ICommonMetadata
        from zeit.content.author.author import update_author_freetext
        content = mock.Mock()
        author1, author2 = mock.Mock(), mock.Mock()
        author1.target.display_name = mock.sentinel.author1
        author2.target.display_name = mock.sentinel.author2
        content.authorships = (author1, author2)
        event = ObjectModifiedEvent(
            content, Attributes(ICommonMetadata, 'authorships'))
        update_author_freetext(content, event)
        self.assertEqual([mock.sentinel.author1, mock.sentinel.author2],
                         content.authors)

    def test_authorships_should_not_be_copied_for_other_field_change(
            self):
        from zope.lifecycleevent import ObjectModifiedEvent, Attributes
        from zeit.cms.content.interfaces import ICommonMetadata
        from zeit.content.author.author import update_author_freetext
        content = mock.Mock()
        content.authors = mock.sentinel.unchanged
        author1, author2 = mock.Mock(), mock.Mock()
        content.authorships = (author1, author2)
        event = ObjectModifiedEvent(
            content, Attributes(ICommonMetadata, 'some-field'))
        update_author_freetext(content, event)
        self.assertEqual(mock.sentinel.unchanged, content.authors)

    def test_authorships_should_clear_authors_when_empty(self):
        from zope.lifecycleevent import ObjectModifiedEvent, Attributes
        from zeit.cms.content.interfaces import ICommonMetadata
        from zeit.content.author.author import update_author_freetext
        content = mock.Mock()
        content.authors = mock.sentinel.unchanged
        content.authorships = ()
        event = ObjectModifiedEvent(
            content, Attributes(ICommonMetadata, 'authorships'))
        update_author_freetext(content, event)
        self.assertEqual([], content.authors)