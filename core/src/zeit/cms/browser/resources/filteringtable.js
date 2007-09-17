/*
 * General Javascript functions
 */


/* tablefilter */
function FilteringTable() {
    this.contentElement = getElementsByTagAndClassName(
        'table', 'contentListing')[0];
    if (this.contentElement == undefined)
        return;
    var tablefilter = getElement('tableFilter');

    connect(this.contentElement, "onclick", this, 'onDataSelect');
    connect(this.contentElement, "ondblclick", this, 'onView');
    connect(tablefilter, 'onkeyup', this, 'updateFilter');
}

FilteringTable.prototype.updateFilter = function(event) {
    var input = event.target();
    var table = this.contentElement;
    var filter_table = this;
    var search_list = this.processSearchInput(input.value);
    var in_what;
    
    forEach(table.rows, function(row) {
        var lastcell = row.cells[row.cells.length - 1];
        if (lastcell.nodeName == 'TH')
            return;
        in_what = lastcell.getElementsByTagName('span')[0].textContent;
        if (filter_table.stringFilter(search_list, in_what)) {
            row.style.display = "table-row";
        } else {
            row.style.display = "none";
        }

    });
}

FilteringTable.prototype.processSearchInput = function(input) {
    return input.toLowerCase().split(' ');
}

FilteringTable.prototype.stringFilter = function(search_for, in_what) {
    in_what = in_what.toLowerCase();
    var word;
    for (var idx in search_for) {
        word = search_for[idx];
        if (!word) {
            continue;
        }
        if (in_what.indexOf(word) == -1) {
            return false;
        }
    }
    return true;
}

// handler fired, when the user selected a table cell
FilteringTable.prototype.onDataSelect = function(event) {
    this.cancelMetadataLoad();
    var tr = event.target().parentNode
    var metadata_url = getFirstElementByTagAndClassName(
        'span', 'Metadata', tr)
    if (!metadata_url)
        return;
    var d = wait(0.1);
    d.addCallback(this.loadMetadataHTML(metadata_url.textContent));
    this.metadata_deferred = d;
     
    var old_selected = this.contentElement.old_selected;
    if (old_selected) {
        removeElementClass(old_selected, 'selected');
    }
    this.contentElement.old_selected = tr;
    addElementClass(tr, 'selected');
}

FilteringTable.prototype.onView = function(event) {
    this.cancelMetadataLoad();
    var tr = event.target().parentNode
    var view_url= getFirstElementByTagAndClassName(
        'span', 'ViewURL', tr)
    if (!view_url)
        return;
    document.location = view_url.textContent;

}


FilteringTable.prototype.loadMetadataHTML = function(url) {
    var d = doSimpleXMLHttpRequest(url);
    d.addCallbacks(
        function(result) {
            var bottomcontent = getElement('bottomcontent');
            var topcontent = getElement('topcontent')

            bottomcontent.innerHTML = result.responseText
            
            addElementClass(topcontent, 'topcontent-small');
            showElement('bottomcontent');
        });
    return d;
}

FilteringTable.prototype.cancelMetadataLoad = function() {
    if (this.metadata_deferred == undefined)
        return;
    this.metadata_deferred.cancel();
    this.metadata_deferred = undefined;
}

var table;
connect(window, 'onload', function() {
  table = new FilteringTable();
});
      
      
// Add-Menu support      
function add_content(menu) {
  var url = menu.options[menu.selectedIndex].value
  if (url.indexOf('http') == -1) {
    return false;
  }
  top.location.href = url
  return true;
}
