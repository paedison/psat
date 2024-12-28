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


function applyTagify() {
    const inputs = document.querySelectorAll('[data-tagify]');
    inputs.forEach(input => {
        if (input.dataset.tagifyApplied) {return}

        const tags = input.getAttribute('data-tags').split(',').map(tag => tag.trim());
        const tagify = new Tagify(input, {
            editTags: false,
            hooks: {
                beforeRemoveTag : tags => {
                    return new Promise((resolve, reject) => {
                        confirm(`'${tags[0].data.value}' 태그를 삭제할까요?`) ? resolve() : reject();
                    });
                }
            }
        });
        tagify.addTags(tags);

        const action = input.getAttribute('data-action');
        const tagTarget = input.getAttribute('data-tag-target');
        function tagifyAction(tagName, tagHeader) {
            htmx.ajax(
                'POST', action,
                {
                    target: tagTarget,
                    swap: 'innerHTML swap:0.25s',
                    values: {'tag': tagName},
                    headers: {'View-Type': tagHeader},
                }
            );
        }

        tagify.on('add', function(e) {tagifyAction(e.detail.data.value, 'add')});
        tagify.on('remove', function(e) {tagifyAction(e.detail.data.value, 'remove')});
        input.dataset.tagifyApplied = 'true';
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

function attachFormHelpTextClass() {
    $('.form-field-container > ul').addClass('list-group list-group-flush mt-1');
    $('.form-field-container > ul > li').addClass('list-group-item small text-danger');
}

function deleteTooltipInner() {
    $('.tooltip-inner').remove();
}

function initializeAll() {
    initializeTooltips();
    initializeSortables();
    initializeToggleButtons();
    applyTagify();
    attachContentCkeditor();
    attachFormHelpTextClass();
    deleteTooltipInner();
}
$(window).on('load', initializeAll);
$(document).on('htmx:afterSettle', initializeAll);

// Disable button while htmx request
$(document).on('htmx:configRequest', function(event) {
    $('.prevent_double_click').prop('disabled', true);
});
$(document).on('htmx:afterRequest', function(event) {
    $('.prevent_double_click').prop('disabled', false);
});
