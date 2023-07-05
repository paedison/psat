import { csrf_token } from './common.js'

let deleteHeader = $('#deleteInstanceModalHeader');
let deleteFooter = $('#deleteInstanceModalFooter');


/* Delete Instance(Post, Comment) */
$(document).on('click', '.delete-instance', function(){
    let text = $(this).data('text');
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    deleteHeader.text(text);
    deleteFooter.attr('href', deleteUrl);
    deleteFooter.data('url', redirectUrl);
});

$(document).on('click', '#deleteInstanceModalFooter', function(event) {
    event.preventDefault();
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    $.ajax({
        url: deleteUrl,
        type: 'POST',
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            $('.close').click();
            window.location.href = redirectUrl;
        }
    });
});


/* Update Comment */
$(document).on('click', '.update-comment', function(event) {
    event.preventDefault();
    let updateUrl = $(this).attr('href');
    let commentId = $(this).data('commentId');
    let target = $(`#comment${commentId}`);
    $.ajax({
        url: updateUrl,
        type: 'GET',
        dataType: 'json',
        headers: { 'X-CSRFToken': csrf_token },
        success: function(data) {
            // let modifiedHtml = data.html.replace('{{ original }}', data.original);
            console.log(data.html);
            if (target.is(':nth-last-child(2)')) {
                target.next().replaceWith(data.html);
                target.next().children('form').append('<input type="hidden" name="csrfmiddlewaretoken" value="' + data.csrf_token + '">');
            } else {
                target.after(data.html);
                target.next().children('form').append('<input type="hidden" name="csrfmiddlewaretoken" value="' + data.csrf_token + '">');
            }
        }
    });
});

