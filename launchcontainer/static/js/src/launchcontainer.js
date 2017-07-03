function getURLOrigin(path) {
  var link = document.createElement('a');
  link.setAttribute('href', path);

  port = (link.port) ? ':'+link.port : '';
  return link.protocol + '//' + link.hostname + port;
}

function LaunchContainerXBlock(runtime, element) {

  $(document).ready(
    function () {

      // This is a template for rendering messages to the user.
      var _notification_template = function ($type, $title, $message) {
        var $iconMap = {'error': 'warning', 'information': 'bullhorn', 'success': 'check'}
        var $renderedTemplate = "<div class='launch-alert launch-alert--"+$type+"'>"
                                + "<span class='icon alert-icon fa fa-"+$iconMap[$type]+"'></span>"
                                  + "<div class='launch-alert--message'>"
                                    + "<h3>"+$title+"</h3>"
                                    + "<p>" 
                                      + $message
                                    + "</p>" 
                                  + "</div>"
                                + "</div>"
        return $renderedTemplate
      }

      // Submit the data to the AVL server and process the response.
      var $launcher = $('#launcher1'),
          $post_url = '{{ API_url|escapejs }}',
          $launcher_form = $('#launcher_form'),
          $launcher_submit = $('#launcher_submit'),
          $launcher_email = $('#launcher_email'),
          $launch_notification = $('#launcher_notification') 

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

        // Add notification message.
        $message = _notification_template(
          'information', 
          'Your request is being processed', 
          'This can take up to 90 seconds--thank you for your patience! '
          + 'If you are having issues, please contact the administrator.'
        )
        $launch_notification.html($message);
        $launch_notification.removeClass('hide');

        // Post the message to the iframe.
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
          $message = _notification_template(
            'success', 'Success', 
            event.data.html_content
          ); 
          $launch_notification.html($message);
          $launch_notification.removeClass('hide');
          $launcher_form.addClass('hide');
        } else if(event.data.status === 'deploymentError') {
          var $status_code = event.data.status_code;
          var $msg;
          if ($status_code === 400) {
            var $errorList = $("<ul class='launch-alert--errorList'>");
            var $errors = event.data.errors;
            for (i=0; i<$errors.length; i++) { 
              $errorList.append($("<li class='launch-alert--errorListItem'>")
                                .text($errors[i][0] + ": " + $errors[i][1][0])
                               ); 
            }
            $msg = $errorList.prop('outerHTML');
          } else if ($status_code === 403) {
            $msg = "Your request failed because the token sent with "
                   + "your request is invalid. "
          } else if ($status_code === 404) {
            $msg = "That project was not found. "; 
          } else if ($status_code === 503) {
            $msg = event.data.errors + " ";
          }
          var $message = _notification_template(
            'error', 'Error', 
            "An error occured in your request: " + $msg + "Please contact the administrator."
          )
            
          $launch_notification.html($message);
          $launch_notification.removeClass('hide');
        }
      }, false);
    });
}
