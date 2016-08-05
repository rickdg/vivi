from zeit.cms.testcontenttype.testcontenttype import TestContentType
from zeit.content.cp.interfaces import IRenderedArea
import lxml.etree
import mock
import pysolr
import zeit.cms.interfaces
import zeit.content.cp.interfaces
import zeit.content.cp.testing
import zeit.edit.interfaces
import zeit.retresco.connection
import zeit.solr.interfaces
import zope.component


class AutomaticAreaSolrTest(zeit.content.cp.testing.FunctionalTestCase):

    def setUp(self):
        super(AutomaticAreaSolrTest, self).setUp()
        self.repository['cp'] = zeit.content.cp.centerpage.CenterPage()
        self.solr = zope.component.getUtility(zeit.solr.interfaces.ISolr)

    def tests_values_contain_only_blocks_with_content(self):
        lead = self.repository['cp']['lead']
        lead.count = 5
        lead.automatic = True
        lead.automatic_type = 'query'
        self.solr.search.return_value = pysolr.Results([], 0)
        self.assertEqual(0, len(IRenderedArea(lead).values()))

    def tests_ignores_items_with_errors(self):
        lead = self.repository['cp']['lead']
        lead.count = 2
        lead.automatic = True
        lead.automatic_type = 'query'

        return_values = [pysolr.Results([
            dict(uniqueId='http://xml.zeit.de/notfound'),
            dict(uniqueId='http://xml.zeit.de/testcontent')], 2),
            pysolr.Results([], 0)
        ]
        self.solr.search.side_effect = lambda *args, **kw: return_values.pop(0)
        self.assertEqual(1, len(IRenderedArea(lead).values()))

    def test_only_marked_articles_are_put_into_leader_block(self):
        self.repository['normal'] = TestContentType()
        leader = TestContentType()
        leader.lead_candidate = True
        self.repository['leader'] = leader

        lead = self.repository['cp']['lead']
        lead.count = 2
        lead.automatic = True
        lead.automatic_type = 'query'

        self.solr.search.return_value = pysolr.Results([
            dict(uniqueId='http://xml.zeit.de/normal'),
            dict(uniqueId='http://xml.zeit.de/leader')], 2)
        result = IRenderedArea(lead).values()
        self.assertEqual(
            'http://xml.zeit.de/leader', list(result[0])[0].uniqueId)
        self.assertEqual(
            'http://xml.zeit.de/normal', list(result[1])[0].uniqueId)

    def test_no_marked_articles_available_leader_block_gets_normal_article(
            self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.automatic_type = 'query'

        self.solr.search.return_value = pysolr.Results([
            dict(uniqueId='http://xml.zeit.de/testcontent')], 1)
        result = IRenderedArea(lead).values()
        leader = result[0]
        self.assertEqual(
            'http://xml.zeit.de/testcontent', list(leader)[0].uniqueId)

    def test_no_marked_articles_leader_block_layout_is_changed_virtually(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.automatic_type = 'query'

        self.solr.search.return_value = pysolr.Results([
            dict(uniqueId='http://xml.zeit.de/testcontent')], 1)
        result = IRenderedArea(lead).values()
        leader = result[0]
        self.assertEqual('buttons', leader.layout.id)
        self.assertEqual('leader', lead.values()[0].layout.id)
        self.assertEllipsis('...module="buttons"...', lxml.etree.tostring(
            zeit.content.cp.interfaces.IRenderedXML(leader),
            pretty_print=True))

    def test_renders_xml_with_filled_in_blocks(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.automatic_type = 'query'

        self.solr.search.return_value = pysolr.Results([
            dict(uniqueId='http://xml.zeit.de/testcontent',
                 lead_candidate=True)], 1)
        xml = zeit.content.cp.interfaces.IRenderedXML(lead)
        self.assertEllipsis(
            """\
<region...>
  <container...type="teaser"...>
    <block...href="http://xml.zeit.de/testcontent"...""",
            lxml.etree.tostring(xml, pretty_print=True))

    def test_rendered_xml_contains_automatic_items_in_cp_feed(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.automatic_type = 'query'

        self.solr.search.return_value = pysolr.Results([
            dict(uniqueId='http://xml.zeit.de/testcontent',
                 lead_candidate=True)], 1)
        xml = zeit.content.cp.interfaces.IRenderedXML(
            self.repository['cp'])
        self.assertEllipsis(
            """...
<feed>
  <reference...href="http://xml.zeit.de/testcontent"...""",
            lxml.etree.tostring(xml, pretty_print=True))

    def test_cms_content_iter_returns_filled_in_blocks(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.automatic_type = 'query'

        self.solr.search.return_value = pysolr.Results([
            dict(uniqueId='http://xml.zeit.de/testcontent',
                 lead_candidate=True)], 1)
        content = zeit.content.cp.interfaces.ICMSContentIterable(lead)
        self.assertEqual(
            ['http://xml.zeit.de/testcontent'],
            [x.uniqueId for x in content])

    def test_stores_query_in_xml(self):
        lead = self.repository['cp']['lead']
        self.assertEqual((), lead.query)
        lead.query = (
            ('Channel', 'International', 'Nahost'),
            ('Channel', 'Wissen', None))
        self.assertEllipsis(
            """<...
            <query>
              <condition...type="Channel"...>International Nahost</condition>
              <condition...type="Channel"...>Wissen</condition>
            </query>...""", lxml.etree.tostring(lead.xml, pretty_print=True))

    def test_prefers_raw_query_if_present(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.raw_query = 'raw'
        lead.automatic_type = 'query'
        self.solr.search.return_value = pysolr.Results([], 0)
        IRenderedArea(lead).values()
        self.assertEqual('raw', self.solr.search.call_args[0][0])

    def test_builds_query_from_conditions(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.query = (
            ('Channel', 'International', 'Nahost'),
            ('Channel', 'Wissen', None),
            ('Keyword', 'Berlin', None))
        lead.automatic = True
        lead.automatic_type = 'channel'
        self.solr.search.return_value = pysolr.Results([], 0)
        IRenderedArea(lead).values()
        query = self.solr.search.call_args[0][0]
        self.assertIn('published:(published*)', query)
        self.assertIn(
            '(channels:(International*Nahost)'
            ' OR channels:(Wissen*)'
            ' OR keywords:(Berlin*))',
            query)

    def test_query_order_defaults_to_semantic_publish(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.query = (('Channel', 'International', 'Nahost'),)
        lead.automatic = True
        lead.automatic_type = 'channel'
        self.solr.search.return_value = pysolr.Results([], 0)
        IRenderedArea(lead).values()
        self.assertEqual(
            'date-last-published-semantic desc',
            self.solr.search.call_args[1]['sort'])

    def test_query_order_can_be_set(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.query = (('Channel', 'International', 'Nahost'),)
        lead.query_order = 'order'
        lead.automatic = True
        lead.automatic_type = 'channel'
        self.solr.search.return_value = pysolr.Results([], 0)
        IRenderedArea(lead).values()
        self.assertEqual('order', self.solr.search.call_args[1]['sort'])

    def test_raw_query_order_defaults_to_first_released(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.raw_query = 'raw'
        lead.automatic_type = 'query'
        self.solr.search.return_value = pysolr.Results([], 0)
        IRenderedArea(lead).values()
        self.assertEqual(
            'date-first-released desc', self.solr.search.call_args[1]['sort'])

    def test_raw_query_order_can_be_set(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.raw_query = 'raw'
        lead.raw_order = 'order'
        lead.automatic_type = 'query'
        self.solr.search.return_value = pysolr.Results([], 0)
        IRenderedArea(lead).values()
        self.assertEqual('order', self.solr.search.call_args[1]['sort'])

    def test_returns_no_content_on_solr_error(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.raw_query = 'raw'
        lead.automatic_type = 'query'
        self.solr.search.side_effect = RuntimeError('provoked')
        self.assertEqual(0, len(IRenderedArea(lead).values()))

    def test_turning_automatic_off_materializes_filled_in_blocks(self):
        self.repository['normal'] = TestContentType()
        leader = TestContentType()
        leader.lead_candidate = True
        self.repository['leader'] = leader

        lead = self.repository['cp']['lead']
        lead.count = 5
        lead.automatic = True
        lead.automatic_type = 'query'
        zope.component.getAdapter(
            lead, zeit.edit.interfaces.IElementFactory, name='rss')()

        empty = pysolr.Results([], 0)
        return_values = [pysolr.Results([
            dict(uniqueId='http://xml.zeit.de/normal'),
            dict(uniqueId='http://xml.zeit.de/leader')], 2),
            empty, empty, empty
        ]
        self.solr.search.side_effect = lambda *args, **kw: return_values.pop(0)
        lead.automatic = False

        result = lead.values()
        self.assertEqual(
            ['teaser', 'teaser', 'rss'], [x.type for x in result])
        self.assertEqual(
            'http://xml.zeit.de/leader', list(result[0])[0].uniqueId)
        self.assertEqual(
            'http://xml.zeit.de/normal', list(result[1])[0].uniqueId)

    def test_checkin_smoke_test(self):
        self.solr.search.return_value = pysolr.Results([], 0)
        with zeit.cms.checkout.helper.checked_out(self.repository['cp']) as cp:
            lead = cp['lead']
            lead.count = 1
            lead.automatic = True
            lead.automatic_type = 'query'

    def test_channel_has_automatic_attribute(self):
        self.solr.search.return_value = pysolr.Results([], 0)
        with zeit.cms.checkout.helper.checked_out(self.repository['cp']) as cp:
            lead = cp['lead']
            lead.count = 1
            lead.automatic = True
            lead.automatic_type = 'query'
        self.assertEqual(
            'True', self.repository['cp.lead'].xml.get('automatic'))


class AutomaticAreaTopicpageTest(zeit.content.cp.testing.FunctionalTestCase):

    def setUp(self):
        super(AutomaticAreaTopicpageTest, self).setUp()
        self.repository['cp'] = zeit.content.cp.centerpage.CenterPage()
        self.tms = mock.Mock()
        self.zca.patch_utility(self.tms, zeit.retresco.interfaces.ITMS)

    def test_passes_id_to_tms(self):
        lead = self.repository['cp']['lead']
        lead.count = 1
        lead.automatic = True
        lead.referenced_topicpage = 'tms-id'
        lead.automatic_type = 'topicpage'
        self.tms.get_topicpage_documents.return_value = (
            zeit.retresco.connection.Result())
        IRenderedArea(lead).values()
        self.assertEqual(
            'tms-id', self.tms.get_topicpage_documents.call_args[0][0])


class AutomaticAreaCenterPageTest(zeit.content.cp.testing.FunctionalTestCase):

    def setUp(self):
        super(AutomaticAreaCenterPageTest, self).setUp()
        self.cp = zeit.content.cp.centerpage.CenterPage()
        self.area = self.cp['feature'].create_item('area')
        self.repository['cp'] = self.cp

        t1 = self.create_content('t1', 't1')
        t2 = self.create_content('t2', 't2')
        t3 = self.create_content('t3', 't3')
        cp_with_teaser = self.create_and_checkout_centerpage(
            name='cp_with_teaser', contents=[t1, t2, t3])
        zeit.cms.checkout.interfaces.ICheckinManager(cp_with_teaser).checkin()

        self.area.referenced_cp = self.repository['cp_with_teaser']
        self.area.count = 3
        self.area.automatic = True
        self.area.automatic_type = 'centerpage'

        self.solr = zope.component.getUtility(zeit.solr.interfaces.ISolr)

    def test_returns_teasers_from_referenced_center_page(self):
        self.assertEqual([
            'http://xml.zeit.de/t1',
            'http://xml.zeit.de/t2',
            'http://xml.zeit.de/t3'],
            [list(x)[0].uniqueId for x in IRenderedArea(self.area).values()])

    def test_yields_centerpage_in_addition_to_teaser_when_iterating(self):
        content = zeit.content.cp.interfaces.ICMSContentIterable(self.cp)
        self.assertEqual([
            u'http://xml.zeit.de/cp_with_teaser',
            u'http://xml.zeit.de/t1',
            u'http://xml.zeit.de/t2',
            u'http://xml.zeit.de/t3'],
            [x.uniqueId for x in content])

    def test_automatic_from_centerpage_requires_referenced_centerpage(self):
        self.area.referenced_cp = None
        with self.assertRaises(zeit.cms.interfaces.ValidationError):
            interface = zeit.content.cp.interfaces.IArea
            self.solr.search.return_value = pysolr.Results([], 0)
            interface.validateInvariants(self.area)

    def test_automatic_using_solr_requires_no_referenced_centerpage(self):
        self.area.referenced_cp = None
        self.area.automatic_type = 'query'
        self.area.raw_query = 'foo'
        with self.assertNothingRaised():
            interface = zeit.content.cp.interfaces.IArea
            self.solr.search.return_value = pysolr.Results([], 0)
            interface.validateInvariants(self.area)


class HideDupesTest(zeit.content.cp.testing.FunctionalTestCase):

    def setUp(self):
        super(HideDupesTest, self).setUp()

        t1 = self.create_content('t1', 't1')
        t2 = self.create_content('t2', 't2')
        t3 = self.create_content('t3', 't3')
        cp_with_teaser = self.create_and_checkout_centerpage(
            name='cp_with_teaser', contents=[t1, t2, t3])
        zeit.cms.checkout.interfaces.ICheckinManager(cp_with_teaser).checkin()

        self.cp = self.create_and_checkout_centerpage()
        self.area = self.create_automatic_area(self.cp)
        self.area.referenced_cp = self.repository['cp_with_teaser']

        self.solr = zope.component.getUtility(zeit.solr.interfaces.ISolr)

    def create_automatic_area(self, cp, count=3, type='centerpage'):
        area = cp['feature'].create_item('area')
        area.count = count
        area.automatic_type = type
        area.automatic = True
        return area

    def test_manual_teaser_already_above_current_area_is_not_shown_again(self):
        self.cp['feature']['lead'].create_item('teaser').append(
            self.repository['t1'])
        self.assertEqual([
            'http://xml.zeit.de/t2',
            'http://xml.zeit.de/t3'
        ], [list(x)[0].uniqueId for x in IRenderedArea(self.area).values()])

    def test_manual_teaser_already_below_current_area_is_not_shown_again(self):
        self.cp['feature'].create_item('area').create_item('teaser').append(
            self.repository['t1'])
        self.assertEqual([
            'http://xml.zeit.de/t2',
            'http://xml.zeit.de/t3'
        ], [list(x)[0].uniqueId for x in IRenderedArea(self.area).values()])

    def test_skipping_duplicate_teaser_retrieves_next_query_result(self):
        self.cp['feature']['lead'].create_item('teaser').append(
            self.repository['t1'])
        self.area.count = 1
        self.assertEqual(
            'http://xml.zeit.de/t2',
            list(IRenderedArea(self.area).values()[0])[0].uniqueId)

    def test_hide_dupes_is_False_then_duplicates_are_not_skipped(self):
        self.cp['feature']['lead'].create_item('teaser').append(
            self.repository['t1'])
        self.area.hide_dupes = False
        self.assertEqual(
            'http://xml.zeit.de/t1',
            list(IRenderedArea(self.area).values()[0])[0].uniqueId)

    def test_already_rendered_area_results_are_cached(self):
        a2 = self.create_automatic_area(self.cp)
        a2.referenced_cp = self.repository['cp_with_teaser']
        a3 = self.create_automatic_area(self.cp)
        a3.referenced_cp = self.repository['cp_with_teaser']

        self.call_count = {}
        real_values = zeit.content.cp.automatic.AutomaticArea.values

        def values_with_count(area):
            self.call_count.setdefault(area.context, 0)
            self.call_count[area.context] += 1
            return real_values(area)

        with mock.patch('zeit.content.cp.automatic.AutomaticArea.values',
                        values_with_count):
            IRenderedArea(a2).values()
            IRenderedArea(a3).values()
        self.assertEqual(1, self.call_count[self.area])

    def test_cp_content_query_filters_duplicates(self):
        lead = self.cp['feature']['lead'].create_item('teaser')
        lead.append(self.repository['t1'])
        lead.append(self.repository['t2'])
        self.assertEqual(
            'http://xml.zeit.de/t3',
            list(IRenderedArea(self.area).values()[0])[0].uniqueId)

    def test_solr_content_query_filters_duplicates(self):
        self.area.automatic_type = 'query'

        lead = self.cp['feature']['lead'].create_item('teaser')
        lead.append(self.repository['t1'])
        lead.append(self.repository['t2'])

        IRenderedArea(self.area).values()
        self.assertEqual(
            'NOT (uniqueId:"http://xml.zeit.de/t2"'
            ' OR uniqueId:"http://xml.zeit.de/t1")',
            self.solr.search.call_args[1]['fq'])
