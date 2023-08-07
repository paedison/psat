import { csrf_token } from './common.js'


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
