function getURLOrigin(path) {
  var link = document.createElement('a');
  link.setAttribute('href', path);

  port = (link.port) ? ':'+link.port : '';
  return link.protocol + '//' + link.hostname + port;
}

function LaunchContainerXBlock(runtime, element) {

  $(document).ready(
    function () {

      var _show_notification = function ($type, $title, $message, $html) {
        // Toggle the message that is shown to the user. 
        $message = $message || undefined; 
        $html = $html || undefined;
        var $iconMap = {'error': 'warning', 'information': 'bullhorn', 'success': 'check'};
        // Segments of a class need to be overwritten, so I just drop all the classes instead
        // of e.g. a regex. 
        // attr() is used instead of removeClass() because a bug in jQuery UI 1.10.0: 
        // https://bugs.jqueryui.com/ticket/9015 
        $('div.launch-alert').attr('class', 'launch-alert launch-alert--' + $type); 
        $('span.launch-alert--icon').attr('class', 'launch-alert--icon fa fa-' + $iconMap[$type]); 
        $('h3.launch-alert--title').text($title);

        if ($message) {
          $('p.launch-alert--body').text($message);
        } else if ($html) {
          // This html only comes from us and ISC, for now. 
          // In the near future we need to remedy this, though, 
          // for Tahoe, by returning.
          $('p.launch-alert--body').html($html);
        };

        $('#launcher_notification').removeClass('is-hidden');
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
        $launcher_email.removeClass('is-hidden');
      }

      $('#launcher_form').submit(function (event) {

        // Shut down the buttons.
        event.preventDefault();
        $launcher_submit.disabled = true; 
        $launcher_submit.text('Launching ...');

        // Add notification message.
        _show_notification(
          'information', 
          'Your request is being processed', 
          'This can take up to 90 seconds--thank you for your patience! '
          + 'If you are having issues, please contact the administrator.'
        )

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
          _show_notification(
            'success', 'Success', null,
            event.data.html_content
          ); 
          $launcher_form.addClass('is-hidden');
        } else if(event.data.status === 'deploymentError') {
          var $status_code = event.data.status_code;
          var $msg;
          if ($status_code === 400) {
            // xx
            var $errorList = $("<ul class='launch-alert--errorList'>");
            var $errors = event.data.errors;
            for (i=0; i<$errors.length; i++) { 
              $errorList.append($("<li class='launch-alert--errorListItem'>")
                                .text($errors[i][0] + ": " + $errors[i][1][0])
                               ); 
            }
            // xx
            $msg = $errorList.prop('outerHTML');
          } else if ($status_code === 403) {
            $msg = "Your request failed because the token sent with "
                   + "your request is invalid. "
          } else if ($status_code === 404) {
            $msg = "That project was not found. "; 
          } else if ($status_code === 503) {
            $msg = event.data.errors + " ";
          }

          _show_notification(
            'error', 'Error', 
            "An error occured in your request: " + $msg + "Please contact the administrator."
          )

        }
      }, false);
    });
}
