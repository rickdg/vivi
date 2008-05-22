"""DAV Connection oriented stuff.

To deprecate resource oriented approach, step by step
"""
import davbase
import davresource
# from dav.davbase import RedirectError
# from dav.davresource import DAVError, DAVLockedError, DAVLockFailedError, \
#                             DAVInvalidLocktokenError, DAVUnlockFailedError

class DAVConnection(davbase.DAVConnection):
    "Extends davbase.DavConnection with a couple of methods"
    # Should be integrated into davbase.DavConnection
    # At the moment we've got the utilities in this file, so
    # our first attempt lives here.
    # not needed (yet):
    #     def __init__(self, *args, **kw):
    #         davbase.DavConnection.__init__(self, args, kw)

    def get_locking_info (self, url):
        """Query the server for locking information.

        The information is returned in a dict, like so
        {'owner': <owner>, 'timeout': <timeout>, 'locktoken': <locktoken>}
        (empty when no lock is on the resource).
        """
        return self._query_lockprop(url).get_locking_info().copy()

    def _query_lockprop (self, url):
        """Query lockdiscovery prop for resource <url>
        """
        # FIXME: we are duplicating some of DAVResource._propfind. Should
        # factor out.
        hdrs = {}
        # FIXME: locktoken? If?
        # FIXME: of course, Ralf's admonition holds:
        #        "Don't use string concatenation to build XML"
        xml = "\n".join(('<?xml version="1.0" encoding="utf-8"?>',
                         '<D:propfind xmlns:D="DAV:">',
                             '<D:prop><D:lockdiscovery /></D:prop>',
                         '</D:propfind>'))
       # NOTE: In the original source they set temporarily (try...finally)
       #       the HTTP version to 1.0. I have no idea what that tries to
       #       accomplish. Leaving out for now.
       # NOTE: We mimic original's behaviour (one redirection). We'd rather
       #       loop until some pre-defined max redirs.
        try:
            response = self.propfind(url, body=xml, depth=0, extra_hdrs="")
        except davbase.RedirectError, err:
            url = err.args[0]
            # re-issue request
            response = self._conn.propfind(url, body=xml, depth=0, extra_hdrs="")
            pass
        davres = davresource.DAVResult(response)
        if davres.status >= 300: # or davres.status in (404,200):
            raise davresource.DAVError, (davres.status, davres.reason, davres)
        return davres

    # Yeah. We might be tempted to override davbase.DAVConnection's
    # lock() and unlock() methods. After reading up on Pathon's super()
    # I just decided to use new names :-/

    def do_lock(self, url, owner=None, depth=0, timeout=None, headers={}):
        r = davresource.DAVResult(self.lock(url,
                                            owner=owner,
                                            depth=depth,
                                            timeout=timeout,
                                            extra_hdrs=headers))
        if not r.has_errors():
            return r.lock_token
        if r.status == 423:
            raise davresource.DAVLockedError, (r,)
        else:
            raise davresource.DAVLockFailedError, (r,)

    def do_unlock(self, url, locktoken, headers={}):
        if not locktoken:
            raise davresource.DAVInvalidLocktokenError
        r = davresource.DAVResult(self.unlock(url,
                                              locktoken,
                                              extra_hdrs=headers))
        if r.has_errors():
            raise davresource.DAVUnlockFailedError, (r,)
        else:
            return
