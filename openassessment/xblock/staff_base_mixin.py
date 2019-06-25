class StaffBaseMixin(object):
    """
    Base Staff mixin with helpers methods.
    """

    def get_user_email(self, anonymous_student_id):
        """
        Gets user_email by anonymous_student_id
        :param anonymous_student_id: string anonymous_student_id
        :return: user_email or None
        """

        try:
            user = self.xmodule_runtime.get_real_user(anonymous_student_id)
            user_email = user.email
        except (TypeError, AttributeError):
            user_email = None

        return user_email
