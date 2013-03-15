$('.search-query').typeahead({
    source: ["cat", "cake"],
    onselect: function(tag) {
        var url = "http://localhost:6543/tag/"
        url += tag
        window.location.href=url
    }
});