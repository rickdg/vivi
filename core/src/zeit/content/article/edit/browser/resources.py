from zeit.cms.browser.resources import Resource, Library
import zeit.cms.browser.resources
import zeit.edit.browser.resources


lib = Library('zeit.content.article', 'resources')

Resource('editor.css')

Resource('replace.js', depends=[
    zeit.cms.browser.resources.base,
])

Resource('editor.js', depends=[
    zeit.cms.browser.resources.base,
    zeit.edit.browser.resources.edit_js,
    zeit.edit.browser.resources.library_js,
    zeit.edit.browser.resources.drop_js,
    zeit.edit.browser.resources.sortable_js,
    zeit.edit.browser.resources.json_js,
    replace_js,
    editor_css,
])

Resource('ads.js', depends=[
    zeit.cms.browser.resources.base,
    editor_js,
])

Resource('counter.js', depends=[zeit.cms.browser.resources.base,
                                zeit.cms.browser.resources.counter_js])
Resource('filename.js', depends=[
    zeit.cms.browser.resources.base,
    zeit.cms.browser.resources.filename_js])
Resource('keyword.js', depends=[zeit.cms.browser.resources.base])
Resource('sync.js', depends=[zeit.cms.browser.resources.base])
Resource('timer.js', depends=[zeit.cms.browser.resources.base])

Resource('blocks.js', depends=[
    zeit.cms.browser.resources.base,
    zeit.edit.browser.resources.edit_js,
    editor_js,
])

Resource('html.js', depends=[
    zeit.cms.browser.resources.base,
    editor_js,
])

Resource('strftime.js')
Resource('jsuri.js')


# XXX zeit.content.article needs zeit.find and zeit.workflow to function,
# should we declare that?
