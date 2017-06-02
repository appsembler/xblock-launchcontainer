from xblock.reference.user_service import UserService, XBlockUser


class MockXBlockUserService(UserService):
    """
    A user service that converts Django users to XBlockUser
    """
    def __init__(self, django_user, **kwargs):
        super(MockXBlockUserService, self).__init__(**kwargs)
        self._django_user = django_user
        if self._django_user:
            self._django_user.user_is_staff = kwargs.get('user_is_staff', False)

    def get_current_user(self):
        """
        Returns the currently-logged in user, as an instance of XBlockUser
        """
        return self._convert_django_user_to_xblock_user(self._django_user)
