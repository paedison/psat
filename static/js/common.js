export const urls = {
    /* Category or Menu */
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
const psat_menu = ['problem', 'like', 'rate', 'answer']

let collapseProblem = $('#collapseProblem');
export let info = JSON.parse($('#info').text());
let menu = info['menu'];
export let csrf_token = $("input[name='csrfmiddlewaretoken']").val();


/* Collapse & activate menu */
function collapseMenu(target) {
    let nav_content = $(target).closest('ul');
    let nav_link = nav_content.prev('a');
    let bullet_point = $(target).children().first()

    nav_link.removeClass('collapsed').attr('aria-expanded', 'true');
    nav_content.addClass('show');
    $(target).addClass('active');
    bullet_point.removeClass('fa-regular').addClass('fa-solid')
}

$(document).ready(function() {
    let target_link = `#${menu}List`
    if (psat_menu.includes(menu)) {
        collapseMenu(target_link);
    } else {
        $(target_link).removeClass('collapsed');
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


/* Ajax for list pagination */
$(document).on('click', '.list-page', function(event) {
    event.preventDefault();
    let url = $(this).attr('href');
    let page = $(this).data('value');
    let target = $(this).closest('section').data('target');
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


/* Ajax for list filter */
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


/* Hide header bar */
$(document).ready(function() {
    let prevScrollPos = $(window).scrollTop();

    $(window).scroll(function() {
        const currentScrollPos = $(window).scrollTop();
        if (prevScrollPos < currentScrollPos) {
            $('.header').addClass('hide');
        } else {
            $('.header').removeClass('hide');
        }
        prevScrollPos = currentScrollPos;
    });
});


// Toggle the side navigation
$("#sidebarToggle").on('click', function(e) {
    $("body").toggleClass("toggle-sidebar");
});
