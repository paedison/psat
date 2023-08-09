import { csrf_token } from './common.js'

let rateButton = $('#rateButton');


/* Ajax for like */
$(document).on('click', '.like-button', function(event) {
    event.preventDefault();
    let url = $(this).attr('href');
    let id = $(this).attr('id');
    let target = `#${id}`;
    $.ajax({
        url: url,
        type: 'POST',
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $(target).replaceWith(data);
        }
    });
});


/* Ajax for rate */
$(document).on('click', '.rate-button', function(){
    let url = $(this).attr('href');
    let id = $(this).attr('id');
    rateButton.data('url', url);
    rateButton.data('target', `#${id}`);
});

$(document).on('click', 'input[name="difficulty"]', function(event) {
    event.preventDefault();
    let difficulty = $(this).attr('value');
    let url = rateButton.data('url');
    let target = rateButton.data('target');
    $.ajax({
        url: url,
        type: 'POST',
        data: { 'difficulty': difficulty },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $('.btn-close').click();
            $(target).replaceWith(data);
        }
    });
});


/* Ajax for answer */
$(document).on('click', '.answer-button', function(event) {
    event.preventDefault();
    let url = $(this).attr('href');
    let target = $(this).data('target');
    let answer = $('input[name="answer"]:checked').val();
    $.ajax({
        url: url,
        type: 'POST',
        data: { 'answer': answer },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $('#answerModalLabel').html(data['message']);
            $(target).replaceWith(data['html']);
        }
    });
});


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


/* Create Memo */
$(document).on('click', '.memo-create-button', function(event) {
    event.preventDefault();
    let createUrl = $(this).data('url');
    let detailMemo = $(`#detailMemo`);
    let user = $('#user_id').val();
    let problem = $('#problem_id').val();
    let content = $('#content').val();
    $.ajax({
        url: createUrl,
        type: 'POST',
        data: {
            'user': user,
            'problem': problem,
            'content': content,
        },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            detailMemo.html(data);
        }
    });
});

/* Load Memo Update Form */
$(document).on('click', '.memo-update', function(event) {
    event.preventDefault();
    let updateUrl = $(this).attr('href');
    let detailMemo = $(`#detailMemo`);
    $.ajax({
        url: updateUrl,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            detailMemo.html(data.html);
        }
    });
});

/* Memo Update */
$(document).on('click', '.memo-update-button', function(event) {
    event.preventDefault();
    let updateUrl = $(this).data('url');
    let user = $('#user_id').val();
    let problem = $('#problem_id').val();
    let content = $('#content').val();
    let detailMemo = $(`#detailMemo`);
    $.ajax({
        url: updateUrl,
        type: 'POST',
        data: {
            'user': user,
            'problem': problem,
            'content': content,
        },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            detailMemo.html(data);
        }
    });
});

/* Instance(Memo) Delete */
$(document).on('click', '.memo-delete', function(){
    let deleteHeader = $('#instanceDeleteModalHeader');
    let deleteFooter = $('#instanceDeleteModalFooter');
    let text = $(this).data('text');
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    deleteHeader.text(text);
    deleteFooter.attr('href', deleteUrl);
    deleteFooter.data('url', redirectUrl);
});

$(document).on('click', '#instanceDeleteModalFooter', function(event) {
    event.preventDefault();
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    $.ajax({
        url: deleteUrl,
        type: 'POST',
        // data: { 'post_id': content },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $('.btn-close').click();
            window.location.href = redirectUrl;
        }
    });
});


/* Create Tag */
$(document).on('click', '.tag-create-button', function(event) {
    event.preventDefault();

    let url = $(this).data('url');
    let target = $(this).data('infoTarget');
    let infoType = $(this).data('infoType');

    let user = $('#user_id').val();
    let problem = $('#problem_id').val();
    let data = $(`#${infoType}`).val();

    $.ajax({
        url: url,
        type: 'POST',
        data: {
            'user': user,
            'problem': problem,
            'tags': data,
        },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $(target).html(data);
            console.log(data);
        }
    });
});

/* Load Tag Update Form */
$(document).on('click', '.tag-update', function(event) {
    event.preventDefault();

    let url = $(this).attr('href');
    let target = $(this).data('infoTarget');
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            $(target).html(data.html);
        }
    });
});

/* Tag Update */
$(document).on('click', '.tag-update-button', function(event) {
    event.preventDefault();

    let url = $(this).data('url');
    let target = $(this).data('infoTarget');
    let infoType = $(this).data('infoType');

    let user = $('#user_id').val();
    let problem = $('#problem_id').val();
    let data = $(`#${infoType}`).val();

    $.ajax({
        url: url,
        type: 'POST',
        data: {
            'user': user,
            'problem': problem,
            'tags': data,
        },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $(target).html(data);
            console.log(data);
        }
    });
});

/* Instance(Tag) Delete */
$(document).on('click', '.tag-delete', function(){
    let deleteHeader = $('#tagDeleteModalHeader');
    let deleteFooter = $('#tagDeleteModalFooter');
    let text = $(this).data('text');
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    deleteHeader.text(text);
    deleteFooter.attr('href', deleteUrl);
    deleteFooter.data('url', redirectUrl);
});

$(document).on('click', '#tagDeleteModalFooter', function(event) {
    event.preventDefault();
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    $.ajax({
        url: deleteUrl,
        type: 'POST',
        // data: { 'post_id': content },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $('.btn-close').click();
            window.location.href = redirectUrl;
        }
    });
});
