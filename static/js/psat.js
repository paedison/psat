import { csrf_token } from './common.js'

/* Ajax for search */
$(document).ready(function() {
    $(document).on('keypress', '#id_data__contains', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            submitSearch();
        }
    });

    $(document).on('click', '#psatSearchButton', function(event) {
        event.preventDefault();
        submitSearch();
    });

    $(document).on('click', '.search-page', function(event) {
        event.preventDefault();
        submitSearch($(this).data('value'));
    });

    function submitSearch(page = null) {
        let psatSearchButton = $('#psatSearchButton')
        let url = psatSearchButton.attr('href');
        let target = psatSearchButton.closest('section').data('target');
        let searchData = {
            'page': page,
            'data__contains': $('#id_data__contains').val()
        };
        $.ajax({
            url: url,
            type: 'POST',
            data: searchData,
            headers: { 'X-CSRFToken': csrf_token },
            success: function(data) {
                $(target).replaceWith(data);
            }
        });
    }
});
