function LaunchContainerEditBlock(runtime, element) {

    console.log($('.xblock-save-button', element));

    function notify(response) {
        var $notificationEl = $('#notification-message'); 
        var $editModal = $('.wrapper.wrapper-modal-window.wrapper-modal-window-edit-xblock');
        var $editModalOverlay = $('.modal-window-overlay');
        var $displayHeader = $('.xblock-header.xblock-header-launchcontainer .header-details');
        var $editSuccessContent = "Your changes have been successfully applied. "
                                  + "Please refresh and then click the button above to test.";
        var $launcherNotification = $('#launcher_notification');

        if (response.result === 'success') {
          // class="ui-loading is-hidden"
          
          // Hide the modal in the Studio interface.
//          $notificationEl.find('span').html('Your request was successful.');
          $editModal.addClass('is-hidden');
          $editModalOverlay.addClass('is-hidden');
          $launcherNotification.text($editSuccessContent);
          $launcherNotification.addClass('ui-state-highlight')
                               .removeClass('ui-state-error')
                               .removeClass('hide');
          $('#launcher_form').removeClass('hide');
        }
        else {
          $notificationEl.addClass('error').removeClass('hide').removeClass('is-hidden');
          $notificationEl.html("It didn't work! "+response.result); 
        }
    }

    $('.save-button', element).bind('click', function() {
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        var data = {
            'project': $('#project_input').val(),
            'project_friendly': $('#project_friendly_input').val(),
            'project_token': $('#project_token_input').val(),
        };

        $.post(handlerUrl, JSON.stringify(data))
          .done(function(response) { 
              notify(response);
        });
    });

    $('.cancel-button', element).bind('click', function() {
        runtime.notify('cancel', {});
    });
}

