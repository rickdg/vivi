from zeit.cms.content.interfaces import ICommonMetadata
from zeit.cms.interfaces import CONFIG_CACHE
from zeit.cms.interfaces import ITypeDeclaration
from zeit.cms.repository.interfaces import IAutomaticallyRenameable
import collections
import grokcore.component as grok
import logging
import requests
import transaction
import zeit.cms.celery
import zeit.cms.checkout.interfaces
import zeit.cms.interfaces
import zope.lifecycleevent


log = logging.getLogger(__name__)


@grok.subscribe(
    zeit.cms.interfaces.ICMSContent,
    zeit.cms.checkout.interfaces.IAfterCheckinEvent)
def notify_after_checkin(context, event):
    # XXX Work around redis/ZODB race condition, see BUG-796.
    for hook in HOOKS:
        notify_webhook.apply_async((context.uniqueId, hook.url), countdown=5)


@grok.subscribe(zope.lifecycleevent.IObjectAddedEvent)
def notify_after_add(event):
    context = event.object
    if not zeit.cms.interfaces.ICMSContent.providedBy(context):
        return
    if zeit.cms.repository.interfaces.IRepository.providedBy(context):
        return
    if zeit.cms.workingcopy.interfaces.IWorkingcopy.providedBy(
            event.newParent):
        return
    for hook in HOOKS:
        notify_webhook.delay(context.uniqueId, hook.url)


@zeit.cms.celery.task(bind=True, queue='webhook')
def notify_webhook(self, uniqueId, url):
    content = zeit.cms.interfaces.ICMSContent(uniqueId, None)
    if content is None:
        log.warning('Could not resolve %s, ignoring.', uniqueId)
        return
    hook = HOOKS.factory.find(url)
    if hook is None:
        log.warning('Hook configuration for %s has vanished, ignoring.', url)
        return
    try:
        hook(content)
    except TechnicalError as e:
        raise self.retry(countdown=e.countdown)
    # Don't even think about trying to write to DAV cache, to avoid conflicts.
    transaction.abort()


class Hook(object):

    def __init__(self, url):
        self.url = url
        self.excludes = []

    def __call__(self, content):
        if self.should_exclude(content):
            return
        log.debug('Notifying %s about %s', self.url, content)
        try:
            self.deliver(content)
        except requests.exceptions.HTTPError as err:
            if getattr(err.response, 'status_code', 500) < 500:
                raise
            else:
                log.warning('Webhook %s returned error, retrying',
                            self.url, exc_info=True)
                raise TechnicalError()
        except requests.exceptions.RequestException:
            log.warning('Webhook %s returned error, retrying',
                        self.url, exc_info=True)
            raise TechnicalError()

    def deliver(self, content):
        r = requests.post(self.url, json=[content.uniqueId], timeout=10)
        r.raise_for_status()

    def add_exclude(self, key, value):
        self.excludes.append((key, value))

    def should_exclude(self, content):
        renameable = getattr(
            IAutomaticallyRenameable(content, None), 'renameable', False)
        if renameable:
            return True
        for exclude in self.excludes:
            if self._matches(exclude, content):
                log.debug('Skipping %s, matched exclude %s', content, exclude)
                return True
        return False

    def _matches(self, exclude, content):
        key, value = exclude
        func = getattr(self, '_match_%s' % key)
        return func(content, value)

    def _match_type(self, content, value):
        typ = getattr(
            ITypeDeclaration(content, None), 'type_identifier', 'unknown')
        return typ == value

    def _match_product(self, content, value):
        if not ICommonMetadata.providedBy(content):
            return False
        return content.product and content.product.id == value


class HookSource(zeit.cms.content.sources.SimpleXMLSource):

    config_url = 'checkin-webhook-config'
    default_filename = 'checkin-webhooks.xml'

    @CONFIG_CACHE.cache_on_arguments()
    def _values(self):
        result = collections.OrderedDict()
        tree = self._get_tree()
        for node in tree.iterchildren('webhook'):
            hook = Hook(node.get('url'))
            for exclude in node.xpath('exclude/*'):
                hook.add_exclude(exclude.tag, exclude.text)
            result[hook.url] = hook
        return result

    def getValues(self):
        return self._values().values()

    def find(self, url):
        return self._values().get(url)


HOOKS = HookSource()


class TechnicalError(Exception):

    def __init__(self, countdown=60):
        self.countdown = countdown
