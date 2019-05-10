function getURLOrigin(path) {
  var link = document.createElement('a');
  link.setAttribute('href', path);
  /* 
  IE 11 will set link.port to string "443" or "80" depending on protocol
  it will also sometimes include ":80" or ":443" in link.host, sometimes not
  (the 'not' case may be just the implementation for IE Dev Tools, but to be sure...)
  */
  var vanilla_ports = ['443', '80', ''];
  var port = (vanilla_ports.indexOf(link.port) == -1 ? ':' + link.port : '');
  return link.protocol + '//' + link.hostname + port;
}

function objectifyForm(formArray) {//serialize data function

  var returnArray = {};
  for (var i = 0; i < formArray.length; i++){
    returnArray[formArray[i]['name']] = formArray[i]['value'];
  }
  return returnArray;
}

function LaunchContainerXBlock(runtime, element) {

  var timeoutMessage;

  $(document).ready(
    function () {

      // Submit the data to the AVL server and process the response. //
      var $launcher = $('#launcher1'),
          $post_url = '{{ API_url|escapejs }}',
          $launcher_form = $('#launcher_form'),
          $launcher_submit = $('#launcher_submit'),
          launcher_submit_text = $launcher_submit.text(),
          $launcher_reset = $('#launcher_reset'),
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

        $user_email = event.target.owner_email.value;
        $project = event.target.project.value;
        $token = event.target.token.value;

        var supportEmail = "{{ support_email }}";
        clearTimeout(timeoutMessage);
        if (supportEmail) {
          timeoutMessage = setTimeout(function() {
            $launch_notification.append(
              '<br /><br />Lab taking a long time to load? Try contacting ' + 
              '<a href="mailto:' + supportEmail + '">' + supportEmail + '</a>'
            );
          }, 120*1000); // show message after 2min
        }

        // Shut down the buttons.
        event.preventDefault();
        $launcher_submit.disabled = true; 
        $launcher_submit.prop('disabled', true)
        $launcher_submit.text('Launching ...');
        $launch_notification.html($waiting);
        $launch_notification.removeClass('hide')
                            .removeClass('ui-state-error')
                            .removeClass('ui-state-notification');
        $launch_iframe = $launcher.find('iframe')[0];
        $launch_iframe.contentWindow.postMessage({
          'project': $project, 
          'owner_email': $user_email,
          'token': $token,
          }, "{{ API_url|escapejs }}"
        );
        return false;
      });

      $('#launcher_reset').click(function (event) {

        var formData = objectifyForm($launcher_form.serializeArray());

        // Shut down the buttons.
        event.preventDefault();
        $.ajax({
            type: "POST",
            url: '{{ API_delete_url|escapejs }}',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            data: JSON.stringify(formData),
            success: function (data) {
              $launcher_form.removeClass('hide');
              $launch_notification.html('<p class="verify-button-success-text" style="font-weight: bold; color: #008200;">\n' +
                '    Your lab has been reset' +
                '</p>');
              $launcher_reset.text('Reset');
              $launcher_submit.text(launcher_submit_text);
              $launcher_submit.disabled = false;
              $launcher_reset.disabled = false;
            }
        });
        $launcher_form.addClass('hide');
        $launcher_reset.text('Resetting...');
        $launcher_submit.disabled = true;
        $launcher_reset.disabled = true;
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
          clearTimeout(timeoutMessage);
          var $status_code = event.data.status_code;
          var $msg;
          var errors = event.data.errors || event.data.detail || "";
          if ($status_code === 400) {
            if (errors instanceof Array) {
              for (i=0; i<errors.length; i++) { 
                $msg = errors[i][0] + ": " + errors[i][1][0] + " "; 
              }
            } else {
              $msg = errors + " ";
            }
          } else if ($status_code === 403) {
            $msg = "Your request failed because the token sent with "
                        +"your request is invalid. "
          } else if ($status_code === 404) {
            $msg = "That project was not found. "; 
          } else if ($status_code === 503) {
            $msg = errors + " ";
          }
          var supportEmail = "{{ support_email }}";
          var $final_msg = "<p class='error'>An error occurred with your request: " + $msg + "</p>"
                           + "<p> Please contact the administrator";
          if (supportEmail) {
            $final_msg += ' at <a href="mailto:' + supportEmail + '">' + supportEmail + '.</a>';
          }
          $final_msg += "</p>"

          $launch_notification.html($final_msg);
          $launch_notification.addClass('ui-state-error').removeClass('hide');
        }
      }, false);
    });
}
