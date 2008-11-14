# Copyright (c) 2007-2008 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.cachedescriptors.property
import zope.component
import zope.formlib.form
import zope.viewlet.viewlet

import zeit.cms.browser.form
import zeit.cms.browser.tree
import zeit.cms.browser.view
import zeit.cms.interfaces
import zeit.cms.repository.interfaces
import zeit.cms.repository.repository
import zeit.cms.workingcopy.interfaces
from zeit.cms.i18n import MessageFactory as _


class Repository(object):

    def __call__(self):
        return zope.component.getUtility(
            zeit.cms.repository.interfaces.IRepository)


class HTMLTree(zope.viewlet.viewlet.ViewletBase):
    """view class for navtree"""

    def render(self):
        return self.index()

    @zope.cachedescriptors.property.Lazy
    def repository(self):
        """repository representing the root of the tree"""
        return zope.component.getUtility(
            zeit.cms.repository.interfaces.IRepository)


class Tree(zeit.cms.browser.tree.Tree):
    """Repository Tree"""

    root_name = 'Repository'
    key = __module__ + '.Tree'

    def listContainer(self, container):
        for obj in sorted(container.values(),
                          key=zeit.cms.content.interfaces.IContentSortKey):
            if not zeit.cms.repository.interfaces.ICollection.providedBy(obj):
                continue
            if (self.preferences.is_hidden(obj)
                and not self.selected(self.getUrl(obj))):
                continue
            yield obj

    @zope.cachedescriptors.property.Lazy
    def root(self):
        """repository representing the root of the tree"""
        return zope.component.getUtility(
            zeit.cms.repository.interfaces.IRepository)

    def isRoot(self, container):
        return zeit.cms.repository.interfaces.IRepository.providedBy(
            container)

    def getUniqueId(self, object):
        if self.isRoot(object):
            return None
        return object.uniqueId

    def selected(self, url):
        view_url = self.request.get('view_url')
        if not view_url:
            view_url = self.request.getURL()

        application_url = self.request.getApplicationURL()
        view_path = view_url[len(application_url):].split('/')
        path = url[len(application_url):].split('/')

        while view_path[-1].startswith('@@'):
            view_path.pop()

        if path > view_path:
            return False

        return view_path[:len(path)] == path

    @zope.cachedescriptors.property.Lazy
    def preferences(self):
        return zeit.cms.repository.interfaces.IUserPreferences(
            zeit.cms.workingcopy.interfaces.IWorkingcopy(
                self.request.principal))

    def expanded(self, obj):
        if self.request.form.get('autoexpand-tree'):
            url = self.getUrl(obj)
            if self.selected(url):
                return True
        return super(Tree, self).expanded(obj)


class HiddenCollections(zeit.cms.browser.view.Base):

    def hide_collection(self):
        self.add_to_preference()
        self.send_message(
            _('"${name}" is now hidden from the navigation tree.',
              mapping=dict(name=self.context.__name__)))
        return self.redirect()

    def show_collection(self):
        self.remove_from_preference()
        self.send_message(
            _('"${name}" is now shown in the navigation tree.',
              mapping=dict(name=self.context.__name__)))
        return self.redirect()

    def redirect(self):
        self.request.response.redirect(self.url(self.context))

    def add_to_preference(self):
        self.preferences.hide_container(self.context)

    def remove_from_preference(self):
        self.preferences.show_container(self.context)

    @property
    def hidden(self):
        return self.preferences.is_hidden(self.context)

    @zope.cachedescriptors.property.Lazy
    def preferences(self):
        return zeit.cms.repository.interfaces.IUserPreferences(
            zeit.cms.workingcopy.interfaces.IWorkingcopy(
                self.request.principal))


class RedirectToObjectWithUniqueId(zeit.cms.browser.view.Base):

    def __call__(self, unique_id, view='@@view.html'):
        # TODO: create a meaningful error message when the object doesn't
        # exist.
        obj = self.repository.getContent(unique_id)
        self.redirect(self.url(obj, view))
        return u''

    @property
    def repository(self):
        return zope.component.getUtility(
            zeit.cms.repository.interfaces.IRepository)
