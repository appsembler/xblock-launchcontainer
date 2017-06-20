function LaunchContainerEditBlock(runtime, element) {

    // Handle the save button click.
    $('.save-button', element).bind('click', function() {
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        var data = {
          'project': $('#project_input').val(),
          'project_friendly': $('#project_friendly_input').val(),
          'project_token': $('#project_token_input').val()
        };

        $.post(handlerUrl, JSON.stringify(data))
          .done(function(response) { 
            if (response.result === 'success') {
            // Update the hidden form and the button text to allow the 
            // user to submit to AVL w/o refreshing.
            // TODO: Can we rely on the RefreshXBlock function 
            // directly to better control this experience? https://git.io/vQIPs
            $('#launcher_project').val(response.validated_data.project);
            $('#launcher_token').val(response.validated_data.project_token);
            $('#launcher_submit').text("Click to launch your " + response.validated_data.project_friendly + "lab");

            // Notify the user of success.
            // This is only available in the Appsembler fork of Open edX, though it 
            // will fail silently elsewhere.
            runtime.notify('save-and-confirm', {
              title: 'Success!',
              message: 'Your AVL project data has been saved. ' 
                + 'Please click the launch button to test.', 
              closeIcon: true, 
              maxShown: 4000
            });

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


