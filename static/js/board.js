import { csrf_token } from './common.js'


// let unsavedChanges = false;
//
// // Detect changes in the title area
// const postTitle = document.getElementById('id_title');
// postTitle.addEventListener('input', function() {
//     unsavedChanges = true;
// });

// let postContents = document.getElementsByClassName('note-editable');
// // Loop through each element and attach the event listener
// for (var i = 0; i < postContents.length; i++) {
//     postContents[i].addEventListener('input', function() {
//         unsavedChanges = true;
//     });
// }

// // Get the target div element
// const postContent = document.getElementById('id_content_iframe');
//
// // Create a new MutationObserver
// const observer = new MutationObserver(function(mutationsList, observer) {
//     unsavedChanges = true;
//     // This function will be called when content changes
//     console.log('Content has changed!');
// });
//
// // Configure the observer to watch for changes in the div's child nodes (content)
// const config = { childList: true };
//
// // Start observing the target div
// observer.observe(postContent, config);
//
//
// // Get all elements with the 'note-editable' class
// const postContents = document.getElementsByClassName('note-editable');
//
// // Create a new MutationObserver for each element
// for (let i = 0; i < postContents.length; i++) {
//     const postContent = postContents[i];
//
//     // Create a new MutationObserver for this element
//     const observer = new MutationObserver(
//         function(mutationsList, observer) {
//         unsavedChanges = true;
//         // This function will be called when content changes
//         console.log('Content has changed!');
//     });
//
//     // Configure the observer to watch for changes in the div's child nodes (content)
//     const config = { childList: true };
//
//     // Start observing this target div
//     observer.observe(postContent, config);
// }

// Display a warning message when leaving the page with unsaved changes
window.addEventListener('beforeunload', function(e) {
    if (unsavedChanges) {
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
});

/* Load Comment Update Form */
$(document).on('click', '.comment-update', function(event) {
    event.preventDefault();
    let updateUrl = $(this).attr('href');
    let commentId = $(this).data('commentId');
    let originalComment = $(`#comment${commentId}`)
    $.ajax({
        url: updateUrl,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            if (originalComment.is(':nth-last-child(2)')) {
                originalComment.next().replaceWith(data.html);
            } else {
                originalComment.after(data.html);
            }
        }
    });
});


/* Comment Update */
$(document).on('click', '.comment-update-button', function(event) {
    event.preventDefault();
    let updateUrl = $(this).data('url');
    let commentId = $(this).data('commentId');
    let content = $('#id_content').val();
    let originalComment = $(`#comment${commentId}`)
    let commentUpdateForm = $(`#commentUpdateForm${commentId}`);
    $.ajax({
        url: updateUrl,
        type: 'POST',
        data: { 'content': content },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            originalComment.replaceWith(data);
            commentUpdateForm.remove();
        }
    });
});


/* Instance(Post, Comment) Delete */
$(document).on('click', '.instance-delete', function(){
    let deleteHeader = $('#instanceDeleteModalHeader');
    let deleteFooter = $('#instanceDeleteModalFooter');
    let text = $(this).data('text');
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    deleteHeader.text(text);
    deleteFooter.attr('href', deleteUrl);
    deleteFooter.data('url', redirectUrl);
});

$(document).on('click', '#instanceDeleteModalFooter', function(event) {
    event.preventDefault();
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    $.ajax({
        url: deleteUrl,
        type: 'POST',
        // data: { 'post_id': content },
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $('.btn-close').click();
            window.location.href = redirectUrl;
        }
    });
});
