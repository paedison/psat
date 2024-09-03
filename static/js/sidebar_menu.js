//#region constants
/** @type {object} info */
const info = JSON.parse($('#info').text());
/** @type {string} info */
const menuCurrent = info['menu'];  // notice, dashboard, official, score
/** @type {string} info */
const menuSelf = info.hasOwnProperty('menu_self') ? info['menu_self'] : '';
/** @type {object} asideNav */
const asideNav = {
    link: function(current) {
        const $this = $(this);
        const isActive = $this.data('menu') === current;
        $this.toggleClass('collapsed', !isActive)
            .attr('aria-expanded', isActive)
            .next('ul').toggleClass('show', isActive);
    },
    icon: function(current, self) {
        const $this = $(this);
        const bullet = $this.children('i').first();
        const isActive = $this.data('menuParent') === current && $this.data('menuSelf') === self;
        $this.toggleClass('active', isActive);
        bullet.toggleClass('fa-solid', isActive).toggleClass('fa-regular', !isActive);
    },
    hide: function() {
        if ($(window).width() < 1200) {
            $('body').removeClass('toggle-sidebar');
        }
    }
}
//#endregion

// Toggle sidebar
$("#sidebarToggle").click(function() {$("body").toggleClass("toggle-sidebar")});

// Hide sidebar when width < 1200
asideNav.hide();

// Hide sidebar when clicked link
$('#main a, #header a').click(function (){asideNav.hide()});

// Default sidebar setting when loaded
$(document).ready(function() {
    $('#sidebar .nav-link').each(function() {asideNav.link.call(this, menuCurrent)});
    $('#sidebar .aside-nav-icon').each(function () {
        asideNav.icon.call(this, menuCurrent, menuSelf)
    });
});

// When clicked the main menu
jQuery('#sidebar .nav-link').click(function () {
    let navContent = $(this).next('ul')
    let dataMenu = $(this).data('menu')
    let dataMenuParent = $(this).data('menuParent')
    let dataMenuSelf = $(this).data('menuSelf')

    $('#sidebar .nav-link').each(function() {
        if (navContent.length) {
            if ($(this).attr('class') === 'nav-link') asideNav.link.call(this, dataMenu)
        } else asideNav.link.call(this, dataMenu)
    });
    $('#sidebar .aside-nav-icon').each(function() {
        asideNav.icon.call(this, dataMenuParent, dataMenuSelf)
    });
    if (!navContent.length) asideNav.hide();
});

// When clicked the sub menu
jQuery('#sidebar .aside-nav-icon').click(function () {
    let dataMenuParent = $(this).data('menuParent')
    let dataMenuSelf = $(this).data('menuSelf')

    $('#sidebar .nav-link').each(function() {asideNav.link.call(this, dataMenuParent)});
    $('#sidebar .aside-nav-icon').each(function() {
        asideNav.icon.call(this, dataMenuParent, dataMenuSelf)
    });
    asideNav.hide();
});

// When clicked the logo
$('#header .logo').click(function() {
    let dataMenu = $(this).data('menu');
    $('#sidebar .nav-link').each(function() {asideNav.link.call(this, dataMenu)});
    $('#sidebar .aside-nav-icon').each(function() {asideNav.icon.call(this, dataMenu, '')});
});
