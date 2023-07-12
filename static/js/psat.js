import { info, urls, csrf_token } from './common.js'

let infoType = info['type'];
let typeUrl = urls[infoType];
let rateButton = $('#rateButton');

let problemChoice = $('#problemChoice');
let selectButton = $('#selectButton');


/* Redirect to problem detail */
selectButton.on('click', () => {
    location.href = `${typeUrl}${problemChoice.val()}/`;
});


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
            $('.close').click();
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
        let url = $('#psatSearchButton').attr('href');
        let target = $('#psatSearchButton').closest('section').data('target');
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
