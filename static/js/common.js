const info = JSON.parse($('#info').text());
const psat_menu = ['problem', 'like', 'rate', 'answer']
const psat_type = ['problemList', 'likeList', 'rateList', 'answerList']
const menu = info['menu'];
const type = info['type'];


// Toggle the side navigation
$("#sidebarToggle").on('click', function() {
    $("body").toggleClass("toggle-sidebar");
});


// Expand & activate menu
function expandMenu(target) {
    const navContent = $(target).closest('ul');
    const navLink = navContent.prev('a');
    const bulletPoint = $(target).children().first();

    navLink.removeClass('collapsed').attr('aria-expanded', 'true');
    navContent.addClass('show');
    $(target).addClass('active');
    bulletPoint.removeClass('fa-regular').addClass('fa-solid');
}

// When clicked the main menu [Notice, Dashboard, PSAT, Schedule, Score]
// menu = notice | dashboard | problem | schedule | score
$(document).ready(function() {
    const targetLink = `#${menu}List`;
    if (psat_menu.includes(menu)) {
        expandMenu(targetLink);
    } else {
        $(targetLink).removeClass('collapsed');
    }
});

// When clicked the PSAT sub-menu [Problem, Like, Rate, Answer]
// type = problem | like | rate | answer
$(document).ready(function() {
    const targetLink = `#${type}`;
    if (psat_type.includes(type)) {
        expandMenu(targetLink);
    } else {
        $(targetLink).removeClass('collapsed');
    }
});


// Initialize the side menu bar
function initialMenu(target) {
    $('.nav-link').addClass('collapsed').attr('aria-expanded', 'false');
    $(target).removeClass('collapsed').attr('aria-expanded', 'true');
    $('#psat-nav').removeClass('show');
    $('.aside-nav-icon').removeClass('active').find('i').removeClass('fa-solid').addClass('fa-regular');

}

// When clicked the logo
$(document).on('click', '.logo', function() {
    initialMenu($(this).data('target'));
    $('body').removeClass('toggle-sidebar');
});

// When clicked the main menu [Notice, Dashboard, PSAT, Schedule, Score]
$(document).on('click', '#sidebar-nav .nav-link', function() {
    initialMenu(this);
    if ($(this).data('bsTarget') !== '#psat-nav') {
        $('body').toggleClass('toggle-sidebar');
    }
});

// When clicked the PSAT sub-menu [Problem, Like, Rate, Answer]
$(document).on('click', '.aside-nav-icon', function() {
    $('.nav-link').addClass('collapsed').attr('aria-expanded', 'false');
    $(this).closest('ul').prev('a').removeClass('collapsed').attr('aria-expanded', 'true');

    $(this).closest('li').children().removeClass('active');
    $(this).closest('li').children().find('i').removeClass('fa-solid').addClass('fa-regular');

    $(this).addClass('active').find('i').removeClass('fa-regular').addClass('fa-solid');
    $('body').toggleClass('toggle-sidebar');
});


// $(document).ready(function() {
//     const targetLink = `#${menu}List`;
//     if (psat_menu.includes(menu)) {
//         expandMenu(targetLink);
//     } else {
//         $(targetLink).removeClass('collapsed');
//     }
// });
//
//
/* Hide header bar */
// $(document).ready(function() {
//     let prevScrollPos = $(window).scrollTop();
//
//     $(window).scroll(function() {
//         const currentScrollPos = $(window).scrollTop();
//         if (prevScrollPos < currentScrollPos) {
//             $('.header').addClass('hide');
//         } else {
//             $('.header').removeClass('hide');
//         }
//         prevScrollPos = currentScrollPos;
//     });
// });

// export const urls = {
//     // Category or Menu
//     'dashboard': '/dashboard/',
//     'profile': '/account/profile/',
//     'problem': '/psat/',
//     'psat': '/psat/',
//     'list': '/psat/',
//     'detail': '/psat/detail/',
//     'like': '/psat/like/',
//     'rate': '/psat/rate/',
//     'answer': '/psat/answer/',
//     'schedule': '/schedule/',
//
//     // Type
//     'dashboardList': '/dashboard/',
//     'profileList': '/account/profile/',
//     'problemList': '/psat/',
//     'problemDetail': '/psat/detail/',
//     'likeList': '/psat/like/',
//     'likeDetail': '/psat/like/',
//     'rateList': '/psat/rate/',
//     'rateDetail': '/psat/rate/',
//     'answerList': '/psat/answer/',
//     'answerDetail': '/psat/answer/',
//     'scheduleList': '/schedule/',
// }
