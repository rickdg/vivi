from zeit.cms.checkout.helper import checked_out
from zeit.content.article.edit.interfaces import IBreakingNewsBody
from zeit.content.article.interfaces import IBreakingNews
from zeit.content.article.testing import create_article
import zeit.content.article.testing


class BreakingNewsTest(zeit.content.article.testing.FunctionalTestCase):

    def test_keywords_are_not_required_for_breaking_news(self):
        article = zeit.content.article.testing.create_article()
        IBreakingNews(article).is_breaking = True
        self.repository['breaking'] = article
        with self.assertNothingRaised():
            with checked_out(self.repository['breaking'], temporary=False):
                pass


class BreakingBannerTest(zeit.content.article.testing.FunctionalTestCase):

    def setUp(self):
        super(BreakingBannerTest, self).setUp()
        self.repository['banner'] = create_article()
        self.repository['article'] = create_article()

    def test_no_a_tag_does_not_match(self):
        with checked_out(self.repository['banner']) as co:
            IBreakingNewsBody(co).text = 'blabla'
        self.assertFalse(
            IBreakingNews(self.repository['article']).banner_matches(
                self.repository['banner']))

    def test_url_equal_uniqueId_matches(self):
        with checked_out(self.repository['banner']) as co:
            IBreakingNewsBody(co).text = (
                '<a href="http://www.zeit.de/article">foo</a>')
        self.assertTrue(
            IBreakingNews(self.repository['article']).banner_matches(
                self.repository['banner']))

    def test_url_not_equal_uniqueId_does_not_match(self):
        with checked_out(self.repository['banner']) as co:
            IBreakingNewsBody(co).text = (
                '<a href="http://www.zeit.de/blub">foo</a>')
        self.assertFalse(
            IBreakingNews(self.repository['article']).banner_matches(
                self.repository['banner']))
