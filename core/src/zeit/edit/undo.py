# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import grokcore.component as grok
import transaction
import zeit.cms.checkout.interfaces
import zeit.connector.interfaces
import zeit.edit.interfaces


UNDOABLE_TRANSACTION = 'zeit.edit.undo: '


class Undo(grok.Adapter):
    """Provides ZODB-based undo (more precisely: reverting all changes up to
    and including a given transaction), but only for a clearly defined scope of
    objects. It reverts:
    - the 'xml' attribute
    - the WebDAVProperties

    This should be all that's needed for objects of the
    zeit.cms.content.interfaces.IXMLContent variety, but please check before
    you apply it to something.

    Only transactions whose description starts with 'zeit.edit.undo: ' are
    considered. This is a string-based interface, so other modules may use this
    without having to depend on us; mark_transaction_undoable() is only
    provided for convenience.
    """

    grok.context(zeit.cms.checkout.interfaces.ILocalContent)
    grok.implements(zeit.edit.interfaces.IUndo)

    @property
    def history(self):
        # XXX how many entries should we ask for?
        history = self._connection.db().history(self.context._p_oid, 20)

        result = []
        for entry in history:
            if not entry['description'].startswith(UNDOABLE_TRANSACTION):
                continue
            description = entry['description'].replace(
                UNDOABLE_TRANSACTION, '', 1)
            result.append(dict(tid=entry['tid'], description=description))
        return result

    def revert(self, tid):
        self._revert_xml(tid)
        self._revert_webdav_properties(tid)

    @property
    def _connection(self):
        return self.context._p_jar

    def _revert_xml(self, tid):
        self.context.xml = self._state_before(self.context, tid)['xml']
        self.context._p_changed = True

    def _revert_webdav_properties(self, tid):
        props = zeit.connector.interfaces.IWebDAVProperties(self.context)
        props.__setstate__(self._state_before(props, tid))
        props._p_changed = True

    def _state_before(self, obj, tid):
        # This is an adapted version of ZODB.Connection.oldstate that uses
        # loadBefore instead of loadSerial (which one might call loadAt), since
        # we can't be sure that/which either the XML or the DAV properties have
        # changed exactly in the given transaction.
        # Unfortunately we have to access the private _reader to unpickle the
        # data record.
        result = self._connection.db().storage.loadBefore(obj._p_oid, tid)
        if result is None:
            raise ValueError('No state of %r before tid %r found' % (obj, tid))
        data, tid, next = result
        return self._connection._reader.getState(data)


def mark_transaction_undoable(action):
    transaction.get().note(UNDOABLE_TRANSACTION + action)
