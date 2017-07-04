function getURLOrigin(path) {
  var link = document.createElement('a');
  link.setAttribute('href', path);

  port = (link.port) ? ':'+link.port : '';
  return link.protocol + '//' + link.hostname + port;
}

function LaunchContainerXBlock(runtime, element) {

  $(document).ready(
    function () {
      // Submit the data to the AVL server and process the response. //
      var $launcher = $('#launcher1'),
          $post_url = '{{ API_url|escapejs }}',
          $launcher_form = $('#launcher_form'),
          $launcher_submit = $('#launcher_submit'),
          $launcher_email = $('#launcher_email'),
          $launch_notification = $('#launcher_notification'), 
          $waiting = 'Your request for a lab is being processed, and may take up to 90 seconds to start. '
          + 'If you are having issues, please contact the administrator.'

      // This is for the xblock-sdk: If there is no email addy, 
      // you can enter it manually.
      if (!$launcher_email.val()) {
        $launcher_email.removeClass('hide');
      }

      $('#launcher_form').submit(function (event) {

        // Shut down the buttons.
        event.preventDefault();
        $launcher_submit.disabled = true; 
        $launcher_submit.text('Launching ...');
        $launch_notification.html($waiting);
        $launch_notification.removeClass('hide')
                            .removeClass('ui-state-error')
                            .removeClass('ui-state-notification');
        $launch_iframe = $launcher.find('iframe')[0];
        $launch_iframe.contentWindow.postMessage({
          'project': "{{ project|escapejs }}",
          'owner_email': "{{ user_email|escapejs }}",
          'token': "{{ project_token|escapejs }}"
          }, "{{ API_url|escapejs }}"
        );
        return false;
      });

      window.addEventListener("message", function (event) {
        if (event.origin !== getURLOrigin('{{ API_url|escapejs }}')) return;
        if(event.data.status === 'siteDeployed') {
          $launch_notification.removeClass('hide')
                              .removeClass('ui-state-error')
                              .html(event.data.html_content);
          // The inner iframe takes care of posting the message, 
          // so we just need to hide the form.
          $launcher_form.addClass('hide');
        } else if(event.data.status === 'deploymentError') {
          var $status_code = event.data.status_code;
          var $msg;
          if ($status_code === 400) {
            var $errors = event.data.errors;
            for (i=0; i<$errors.length; i++) { 
              $msg = $errors[i][0] + ": " + $errors[i][1][0] + " "; 
            }
          } else if ($status_code === 403) {
            $msg = "Your request failed because the token sent with "
                        +"your request is invalid. "
          } else if ($status_code === 404) {
            $msg = "That project was not found. "; 
          } else if ($status_code === 503) {
            $msg = event.data.errors + " ";
          }
          var $final_msg = "<p class='error'>An error occured in your request: " + $msg + "</p>" 
                           + "<p> Please contact the administrator.</p>";
          $launch_notification.html($final_msg);
          $launch_notification.addClass('ui-state-error').removeClass('hide');
        }
      }, false);
    });
}
