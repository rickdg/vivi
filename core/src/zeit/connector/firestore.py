
import zope
import zope.interface
import six
from six.moves.urllib.parse import urlparse
from google.cloud import datastore
from interfaces import IConnector
from io import BytesIO

import zeit.connector.resource


@zope.interface.implementer(zeit.connector.interfaces.IConnector)
class Firestore(object):
    def __init__(self, project_id="zeitonline-main", namespace='zeit.web',
                 entity_type='generic_document'):
        self.client = datastore.Client(project_id, namespace=namespace)
        self.entity_type = entity_type

    @staticmethod
    def _id_splitlast(id):
        # Split id in parent/name parts
        # FIXME fix borderline cases: _splitlast(""), _splitlast("/")
        parent, last = id.rstrip('/').rsplit('/', 1)
        if id.endswith('/'):
            last = last + '/'
        return parent + '/', last

    def __getitem__(self, id):
        query = self.client.query(kind=self.entity_type)
        query.add_filter('metadata.meta.url', '=', urlparse(id).path)
        result = list(query.fetch(1))

        if len(result) < 1:
            raise KeyError(id)

        result = result[0]

        return zeit.connector.resource.Resource(
            six.text_type(id), self._id_splitlast(id)[1].rstrip('/'),
            result['metadata']['meta']['type'],
            BytesIO(('<article><head/>%s</article>' % result['body']).encode('utf-8')),
            self._get_properties(result['metadata']),
            '')

    def _get_properties(self, metadata):
        result = {}
        for namespace in metadata.keys():
            for name in metadata[namespace]:
                result.update({
                    (name, namespace): metadata[namespace][name]
                })
        return result
