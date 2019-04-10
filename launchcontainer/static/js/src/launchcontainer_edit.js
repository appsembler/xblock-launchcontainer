function LaunchContainerEditBlock(runtime, element) {

    // Handle the save button click.
    $('.save-button', element).bind('click', function() {
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        var data = {
          'enable_container_resetting': $('#enable_container_resetting_input').val(),
          'project': $('#project_input').val(),
          'project_friendly': $('#project_friendly_input').val(),
          'project_token': $('#project_token_input').val(),
          'support_email': $('#support_email_input').val(),
        };

        $.post(handlerUrl, JSON.stringify(data))
          .done(function(response) { 
            if (response.result === 'success') {
              // We force the page to reload because the XBlock runtime 
              // doesn't handle this properly if your are in a unit: https://git.io/vQ4Kj.
              window.location.reload();
            } else {
              runtime.notify('error', {message: 'Error: '+response.result});
            }
          });
    });

    // Handle the cancel button click.
    $('.cancel-button', element).bind('click', function() {
        runtime.notify('cancel', {});
    });

    // Allow the escape key to close the XBlock form.
    $(document).keyup(function(e) {
      if (e.keyCode == 27) {
        runtime.notify('cancel');
      }
    });
}
