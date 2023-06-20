let urls = {
    /* Category */
    'dashboard': '/dashboard/',
    'profile': '/account/profile/',
    'problem': '/psat/',
    'psat': '/psat/',
    'list': '/psat/',
    'detail': '/psat/detail/',
    'like': '/psat/like/',
    'rate': '/psat/rate/',
    'answer': '/psat/answer/',
    'schedule': '/schedule/',

    /* Type */
    'dashboardList': '/dashboard/',
    'profileList': '/account/profile/',
    'problemList': '/psat/',
    'problemDetail': '/psat/detail/',
    'likeList': '/psat/like/',
    'likeDetail': '/psat/like/',
    'rateList': '/psat/rate/',
    'rateDetail': '/psat/rate/',
    'answerList': '/psat/answer/',
    'answerDetail': '/psat/answer/',
    'scheduleList': '/schedule/',
}

let rateButton = $('#rateButton');

/* Activating Menu */
let collapseProblem = $('#collapseProblem');
let info = JSON.parse($('#info').text());
let infoCategory = info['category'];
let infoType = info['type'];
// let infoUrl = info['url'];
let infoTitle = info['title'];

let categoryUrl = urls[infoCategory];
let typeUrl = urls[infoType];

let csrf_token = $("input[name='csrfmiddlewaretoken']").val();

/* Collapse Menu */
function collapseMenu() {
    collapseProblem.parent().addClass('active');
    collapseProblem.prev('a').removeClass('collapsed');
    collapseProblem.addClass('show');
}

$(document).ready(function() {
    $('#' + infoCategory + 'List').addClass('active');
    if (infoCategory === 'problem'
        || infoCategory === 'like'
        || infoCategory === 'rate'
        || infoCategory === 'answer'
    ) {
        collapseMenu();
    }
});

// $(document).ready(function() {
//     switch (infoCategory) {
//         case 'problem':
//             $("#problemList").addClass("active");
//             collapseMenu()
//             break;
//         case 'like':
//             $("#likeList").addClass("active");
//             collapseMenu()
//             break;
//         case 'rate':
//             $("#rateList").addClass("active");
//             collapseMenu()
//             break;
//         case 'answer':
//             $('#answerList').addClass('active');
//             collapseMenu()
//             break;
//         case 'qna':
//             $("#communityList").addClass("active");
//             collapseMenu()
//             break;
//         case 'dashboard':
//             $('#dashboard').addClass('active');
//             break;
//         case 'schedule':
//             $('#schedule').addClass('active');
//             break;
//         case 'profile':
//             $('#Profile').addClass('active');
//             break;
//         case 'account':
//             $('#Profile').addClass('active');
//             break;
//     }
// });

/* Logout */
$(document).on('click', '#accountLogout', function() {
    event.preventDefault();
    let url = $(this).attr('href');
    $.ajax({
        url: url,
        type: 'POST',
        data: {
        },
        headers: { 'X-CSRFToken': csrf_token },
        success: function() {
              window.location.href = urls['psat'];
        }
    });
});

/* Image Click to Close */
$(document).on('click', '.problem-image', function() {
    $.ajax({
        url: '/log/request/',
        type: 'POST',
        data: {
            'info': info,
            'extra': '(Close)',
        },
        headers: { 'X-CSRFToken': csrf_token },
        success: function() {
            window.close();
        }
    });
});

/* Ajax for '.list-page' (Problem / Like / Rate / Answer List Pagination) */
$(document).on('click', '.list-page', function(event) {
    event.preventDefault();
    let url = $(this).attr('href');
    let page = $(this).data('value');
    let target = $(this).closest('div').data('target');
    $.ajax({
        url: url,
        type: 'POST',
        data: { 'page': page },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $(target).replaceWith(data);
        }
    });
});

/* Ajax for '.list-filter' (Like / Rate / Answer List Filter) */
$(document).on('click', '.list-filter', function(event) {
    event.preventDefault();
    let url = $(this).attr('href');
    let target = $(this).closest('div').data('target');
    $.ajax({
        url: url,
        type: 'POST',
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $(target).replaceWith(data);
        }
    });
});

// /* Ajax for '.rate-like-page' (Rate Card Pagination) */
// $(document).on('click', '.card-rate-page', function(event) {
//     event.preventDefault();
//     let page = $(this).data('value');
//     let url = `${infoUrl}rate/`
//     $.ajax({
//         url: url,
//         type: 'POST',
//         data: { 'page': page },
//         headers: { 'X-CSRFToken': csrf_token },
//         success: function(data) {
//             $('#cardRate').html(data);
//         }
//     });
// });
//
// /* Ajax for '.answer-like-page' (Answer Card Pagination) */
// $(document).on('click', '.card-answer-page', function(event) {
//     event.preventDefault();
//     let page = $(this).data('value');
//     let url = `${infoUrl}answer/`
//     $.ajax({
//         url: url,
//         type: 'POST',
//         data: { 'page': page },
//         headers: { 'X-CSRFToken': csrf_token },
//         success: function(data) {
//             $('#cardAnswer').html(data);
//         }
//     });
// });


///////////////////////////////////////////
///////////////////////////////////////////
///////////////////////////////////////////
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

