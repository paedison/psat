export const urls = {
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

let collapseProblem = $('#collapseProblem');
let info = JSON.parse($('#info').text());
let infoCategory = info['category'];
export let csrf_token = $("input[name='csrfmiddlewaretoken']").val();


/* Collapse & Activate Menu */
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


/* Logout */
$(document).on('click', '#accountLogout', function(event) {
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
