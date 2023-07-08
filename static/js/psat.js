import { info, urls, csrf_token } from './common.js'

let infoType = info['type'];
let typeUrl = urls[infoType];
let rateButton = $('#rateButton');

let problemChoice = $('#problemChoice');
let selectButton = $('#selectButton');


/* */
selectButton.on('click', () => {
    location.href = `${typeUrl}${problemChoice.val()}/`;
});


/* Ajax for '#rateButton' (Rate Button) */
$(document).on('click', '#problemChoice input[name="difficulty"]', function(event) {
    event.preventDefault();
    let difficulty = $(this).attr('value');
    let url = rateButton.data('url');
    let target = '#' + rateButton.data('target');
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


/* Ajax for '.list-filter' (Like / Rate / Answer List Filter) */
$(document).on('click', '.list-filter', function(event) {
    event.preventDefault();
    let url = $(this).attr('href');
    let target = $(this).closest('section').data('target');
    $.ajax({
        url: url,
        type: 'POST',
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $(target).replaceWith(data);
        }
    });
});


/* Ajax for '.like-button' (Like Button) */
$(document).on('click', '.like-button', function(event) {
    event.preventDefault();
    let url = $(this).attr('href');
    let target = $(this).data('target');
    $.ajax({
        url: url,
        type: 'POST',
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $(target).replaceWith(data);
        }
    });
});


/* Transmitting Data for '.rate-button' (Open Rate Modal) */
$(document).on('click', '.rate-button', function(){
    let problemId = $(this).data('problemId');
    let url = $(this).attr('href');
    let id = $(this).attr('id');
    rateButton.data('url', url);
    rateButton.data('target', id);
});

/* Ajax for '#rateButton' (Rate Button) */
$(document).on('click', 'input[name="difficulty"]', function(event) {
    event.preventDefault();
    let difficulty = $(this).attr('value');
    let url = rateButton.data('url');
    let target = '#' + rateButton.data('target');
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


/* Ajax for '.answer-button' (Answer Button) */
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

