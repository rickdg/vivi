from zeit.cms.interfaces import ICMSContent
from zeit.content.article.interfaces import IArticle
import argparse
import logging
import prometheus_client
import zeit.cms.cli
import zeit.find.interfaces
import zeit.retresco.interfaces
import zope.component


REGISTRY = prometheus_client.CollectorRegistry()
log = logging.getLogger(__name__)


class Metric:

    def __init__(self, name, query=None, es=None):
        super().__init__(name, '', registry=REGISTRY)
        self.query = query
        self.es = es


class Gauge(Metric, prometheus_client.Gauge):
    pass


class Counter(Metric, prometheus_client.Counter):
    pass


IMPORTERS = [
    Gauge('vivi_recent_news_published_total', [
        {'term': {'payload.workflow.product-id': 'News'}},
        {'range': {'payload.document.date-last-modified': {'gt': 'now-1h'}}},
    ], 'external'),
    Gauge('vivi_recent_videos_published_total', [
        {'term': {'doc_type': 'video'}},
        {'range': {'payload.document.date-last-modified': {'gt': 'now-1h'}}},
    ], 'external'),
    Gauge('vivi_recent_vgwort_reported_total', [
        {'range': {'payload.vgwort.reported_on': {'gt': 'now-1h'}}},
    ], 'internal'),
]
TOKEN_COUNT = Gauge('vivi_available_vgwort_tokens_total')
BROKEN = Counter('vivi_articles_with_missing_tms_authors', {
    'query': {'bool': {'filter': [
        {'term': {'doc_type': 'article'}},
        {'range': {'payload.document.date_first_released': {'gt': 'now-30m'}}}
    ]}},
    '_source': ['url', 'payload.head.authors'],
}, 'external')


@zeit.cms.cli.runner()
def collect():
    """Collects all app-specific metrics that we have. Mostly these are based
    on ES queries, but not all of them. This is probably *not* the best
    factoring, but the overall amount is so little that putting in a larger
    architecture/mechanics is just not worth it at this point.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('pushgateway')
    options = parser.parse_args()

    elastic = {
        'external': zope.component.getUtility(
            zeit.retresco.interfaces.IElasticsearch),
        'internal': zope.component.getUtility(
            zeit.find.interfaces.ICMSSearch),
    }
    for metric in IMPORTERS:
        query = {'query': {'bool': {'filter': metric.query}}}
        es = elastic[metric.es]
        metric.set(es.search(query, rows=0).hits)

    tokens = zope.component.getUtility(zeit.vgwort.interfaces.ITokens)
    TOKEN_COUNT.set(len(tokens))

    for row in elastic[BROKEN.es].search(BROKEN.query, rows=100):
        content = ICMSContent('http://xml.zeit.de' + row['url'], None)
        if not IArticle.providedBy(content):
            log.info('Skip %s, not found', row['url'])
            continue
        tms = row.get('payload', {}).get('head', {}).get('authors', [])
        for ref in content.authorships:
            id = ref.target_unique_id
            if id and id not in tms:
                log.warn('%s: author %s not found in TMS', content, id)
                BROKEN.inc()

    prometheus_client.push_to_gateway(
        options.pushgateway, job=__name__, registry=REGISTRY)
