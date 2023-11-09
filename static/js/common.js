const info = JSON.parse($('#info').text());
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

// When the main menu activated [Notice, Dashboard, PSAT, Schedule, Score]
// menu = notice | dashboard | psat | schedule | score
$(document).ready(function() {
    if (menu === 'psat') {
        const view_type = info['view_type'];
        expandMenu(`#${view_type}List`);
    }
    else {
        $(`#${menu}List`).removeClass('collapsed');
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
    if ($(window).width() < 1200) {
        $('body').removeClass('toggle-sidebar');
    }
});

// When clicked the main menu [Notice, Dashboard, PSAT, Schedule, Score]
$(document).on('click', '#sidebar-nav .nav-link', function() {
    const menu_id = ['#psat-nav', '#score-nav']
    let bsTarget = $(this).data('bsTarget')
    initialMenu(this);
    if (!menu_id.includes(bsTarget)) {
    // if ($(this).data('bsTarget') !== '#psat-nav') {
        if ($(window).width() < 1200) {
            $('body').removeClass('toggle-sidebar');
        }
    }
});

// When clicked the PSAT sub-menu [Problem, Like, Rate, Answer]
$(document).on('click', '.aside-nav-icon', function() {
    $('.nav-link').addClass('collapsed').attr('aria-expanded', 'false');
    $(this).closest('ul').prev('a').removeClass('collapsed').attr('aria-expanded', 'true');

    $(this).closest('li').children().removeClass('active');
    $(this).closest('li').children().find('i').removeClass('fa-solid').addClass('fa-regular');

    $(this).addClass('active').find('i').removeClass('fa-regular').addClass('fa-solid');
    if ($(window).width() < 1200) {
        $('body').removeClass('toggle-sidebar');
    }
});
