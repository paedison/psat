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

export let info = JSON.parse($('#info').text());
let menu = info['menu'] || $('#info').text();
export let csrf_token = $("input[name='csrfmiddlewaretoken']").val();


/* Expand & activate menu */
function expandMenu(target) {
    const navContent = $(target).closest('ul');
    const navLink = navContent.prev('a');
    const bulletPoint = $(target).children().first();

    navLink.removeClass('collapsed').attr('aria-expanded', 'true');
    navContent.addClass('show');
    $(target).addClass('active');
    bulletPoint.removeClass('fa-regular').addClass('fa-solid');
}

$(document).on('click', '.nav-link', function() {
    $('.nav-link').addClass('collapsed').attr('aria-expanded', 'false');
    $(this).removeClass('collapsed').attr('aria-expanded', 'true');
    $('#psat-nav').removeClass('show');
    $('.aside-nav-icon').removeClass('active').find('i').removeClass('fa-solid').addClass('fa-regular');
});

$(document).on('click', '.aside-nav-icon', function() {
    $('.nav-link').addClass('collapsed').attr('aria-expanded', 'false');
    $(this).closest('ul').prev('a').removeClass('collapsed').attr('aria-expanded', 'true');

    $(this).closest('li').children().removeClass('active');
    $(this).closest('li').children().find('i').removeClass('fa-solid').addClass('fa-regular');

    $(this).addClass('active').find('i').removeClass('fa-regular').addClass('fa-solid');
});

$(document).ready(function() {
    const targetLink = `#${menu}List`;
    if (psat_menu.includes(menu)) {
        expandMenu(targetLink);
    } else {
        $(targetLink).removeClass('collapsed');
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
$("#sidebarToggle").on('click', function() {
    $("body").toggleClass("toggle-sidebar");
});
