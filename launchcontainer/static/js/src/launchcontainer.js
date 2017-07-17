function getURLOrigin(path) {
  var link = document.createElement('a');
  link.setAttribute('href', path);

  port = (link.port) ? ':'+link.port : '';
  return link.protocol + '//' + link.hostname + port;
}

function LaunchContainerXBlock(runtime, element) {

  $(document).ready(
    function () {

      var _show_notification = function (type, params) {
        // Toggle the message that is shown to the user. 
        
        var title = params.title, 
            textMessage = params.textMessage || undefined, 
            htmlMessage = params.htmlMessage || undefined, 
            errors = params.errors || undefined,
            iconMap = {
              'error': 'warning', 
              'information': 'bullhorn', 
              'success': 'check'
            };

        // Segments of a class need to be overwritten, so I just drop all the classes instead
        // of e.g. a regex. 
        // attr() is used instead of removeClass() because a bug in jQuery UI 1.10.0: 
        // https://bugs.jqueryui.com/ticket/9015 
        $('div.launch-alert').attr('class', 'launch-alert launch-alert--' + type); 
        $('span.launch-alert--icon').attr('class', 'launch-alert--icon fa fa-' + iconMap[type]); 
        $('h3.launch-alert--title').text(title);

        if (textMessage) {
          $('p.launch-alert--body').text(textMessage);
        } else if (htmlMessage) {
          // This html only comes from us and ISC, for now. 
          // In the near future we need to remedy this, though, 
          // for Tahoe, by modifying the Wharf interface to disallow html, 
          // or use Django to sanitize it?
          $('p.launch-alert--body').html(htmlMessage);
        }

        if (errors) {
          var errorListItems = [], 
              errorListEl = $('.launch-alert--errorListItem')[0];
          for (i=0; i<$errors.length; i++) { 
            errorListItems.append($(errorListEl).clone()
              .text($errors[i][0] + ": " + $errors[i][1][0])
              .removeClass('is-hidden')
            );
          }
          $('ul.launch-alert--errorList').append(errorItems).removeClass('is-hidden');
        }

        $('#launcher_notification').removeClass('is-hidden');
      };

      // Submit the data to the AVL server and process the response.
      var $launcher = $('#launcher1'),
          $post_url = '{{ API_url|escapejs }}',
          $launcher_submit = $('#launcher_submit'),
          $launcher_email = $('#launcher_email'),
          $launch_notification = $('#launcher_notification');

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
          'information', {
            title: 'Your request is being processed', 
            textMessage: 'This can take up to 90 seconds--thank you for your patience! ' + 
                         'If you are having issues, please contact the administrator.'
          }
        );

        // Post the message to the iframe.
        $launch_iframe = $launcher.find('iframe')[0];
        $launch_iframe.contentWindow.postMessage({
//          'project': "{{ project|escapejs }}",
          'owner_email': "{{ user_email|escapejs }}",
          'token': "{{ project_token|escapejs }}"
          }, "{{ API_url|escapejs }}"
        );
        return false;
      });

      window.addEventListener("message", function (event) {
        if (event.origin !== getURLOrigin('{{ API_url|escapejs }}')) return;
        if (event.data.status === 'siteDeployed') {
          _show_notification(
            'success', {
              title: 'Success', 
              htmlMessage: event.data.html_content
            }
          ); 
          $('.launcher-form--container').addClass('is-hidden');
        } else if (event.data.status === 'deploymentError') {
          $('.launcher-form--container').addClass('is-hidden');

          var status_code = event.data.status_code,
              title = 'Error',
              errorMessage = "There was an error in your request. Please contact " + 
                             "the support team, or reload the page and try again.",
              errors;

          switch (status_code) {
            case 400:
            case 503:
              errors = event.data.errors;
              break;
            case 403:
              // These wonky structures are the way that we match DRF's errors.
              errors = [
                [
                  '', 
                  [['Your request failed because the token you sent with the request is invalid.']]
                ]
              ];
              break;
            case 404:
              errors = [
                [
                  '', 
                  [['That project was not found.']]
                ]
              ];
          }

          _show_notification(
            'error', { 
              title: title, 
              textMessage: errorMessage, 
              errors: errors 
            }
          );

        }
      }, false);
    });
}
