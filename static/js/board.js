let deleteInstanceModalHeader = $('#deleteInstanceModalHeader');
let deleteInstanceModalFooter = $('#deleteInstanceModalFooter');
let csrf_token = $("input[name='csrfmiddlewaretoken']").val();

/* Delete Instance(Post, Comment) */
$(document).on('click', '#deleteInstance', function(){
    let text = $(this).data('text');
    let deleteUrl = $(this).attr('href');
    let redirectUrl = $(this).data('url');
    deleteInstanceModalHeader.text(text);
    deleteInstanceModalFooter.attr('href', deleteUrl);
    deleteInstanceModalFooter.data('url', redirectUrl);
    console.log(deleteInstanceModalFooter.data('url'));
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
