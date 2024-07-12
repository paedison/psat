const info = JSON.parse($('#info').text());
const menu = info['menu'];  // notice, dashboard, psat, score, schedule
const view_type = info['view_type'];  // problem, like, rate, solve, search, psatScore, primeScore
const parent_menu = ['score']  // menu with child branches

// Toggle the side navigation
$("#sidebarToggle").click(function() {
    $("body").toggleClass("toggle-sidebar");
});

function hideSidebar() {
    if ($(window).width() < 1200) {
        $('body').removeClass('toggle-sidebar');
    }
}

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

// Initialize the side menu bar
function initialMenu() {
    $('.nav-link').addClass('collapsed').attr('aria-expanded', 'false');
    $('.aside-nav-icon').removeClass('active').find('i').removeClass('fa-solid').addClass('fa-regular');
}

// When the main menu activated
$(document).ready(function() {
    if (parent_menu.includes(menu)) {
        expandMenu(`#${view_type}List`);
    }
    else {
        $(`#${menu}List`).removeClass('collapsed');
    }
});

// When clicked the logo
$('.logo').click(function() {
    let target = $(this).data('target');
    initialMenu();
    $(target).removeClass('collapsed').attr('aria-expanded', 'true');
    hideSidebar();
});

// When clicked the main menu
$('#noticeList, #dashboardList, #psatList, #predictList, #scheduleList, #lectureList').click(function() {
    initialMenu();
    $(this).removeClass('collapsed').attr('aria-expanded', 'true');
    hideSidebar()
});

// When clicked the sub-menu
jQuery('.aside-nav-icon').click(function() {
    initialMenu();

    $(this).closest('ul').prev('a').removeClass('collapsed').attr('aria-expanded', 'true');
    $(this).closest('li').children().removeClass('active');
    $(this).closest('li').children().find('i').removeClass('fa-solid').addClass('fa-regular');

    $(this).addClass('active').find('i').removeClass('fa-regular').addClass('fa-solid');
    hideSidebar();
});

// Initialize tooltips, Sortables, toggleButtons
function initializeTooltips() {
    $('[data-bs-toggle="tooltip"]').tooltip();
}

function initializeSortables() {
    $('.sortable').each(function() {
        new Sortable(this, {
            animation: 150,
            ghostClass: 'blue-background-class'
        });
    });
}

function initializeToggleButtons() {
    $('#toggleProblemBtn, #toggleCommentBtn, #floatingCollectionIndicator').click(function () {
        $('#floatingCollection').removeClass('show-menu');
        $('#toggleCollectionBtn').show().animate({right: '20'}, 300);
    });
    $('#toggleCollectionBtn').click(function() {
        $('#floatingCollection').addClass('show-menu');
        $(this).hide();
    });
}

// Attach the content of ckeditor to the form
function attachContentCkeditor() {
    $('.ckeditor-submit').click( function() {
        let button = $(this);
        let ckeditorId = button.closest('form').find('div.django-ckeditor-widget').attr('data-field-id');
        let content = CKEDITOR.instances[ckeditorId].getData();
        button.closest('form').find('textarea.ckeditor-content').text(content);
    });
}

function scrollToTop() {
    $('html, body').animate({ scrollTop: 0 }, 'fast');
}

function mainAnchorClick() {
    $('#main a').click(function (){
        hideSidebar();
    });
}

initializeTooltips();
initializeSortables();
initializeToggleButtons();
attachContentCkeditor();
mainAnchorClick();

jQuery('body').on('htmx:afterSwap', function() {
    // scrollToTop();
    initializeTooltips();
    initializeSortables();
    initializeToggleButtons();
    attachContentCkeditor();
    mainAnchorClick();
});

// Disable button while htmx request
$(document).on('htmx:configRequest', function(event) {
    $('.prevent_double_click').prop('disabled', true);
});
$(document).on('htmx:afterRequest', function(event) {
    $('.prevent_double_click').prop('disabled', false);
});
