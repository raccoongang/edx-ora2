import datetime
import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from opaque_keys.edx.keys import CourseKey, UsageKey

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from courseware.url_helpers import get_redirect_url

log = logging.getLogger(__name__)


def send_notification_email(user_email, submission):
    """
    Util function that send notification email to learner about status his/her assessment

    Email sends after staff `cancel_submission`, `return_submission` and `done_submission` actions.
    :type user_email: string User email
    :param submission: object submission of user assessment
    """
    from_email = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)

    url = get_redirect_url(
        CourseKey.from_string(submission['student_item']['course_id']),
        UsageKey.from_string(submission['student_item']['item_id'])
    )

    email_params = {
        'url': url,
        'staff_message': submission['student_item']['item_id'],
        'datetime': datetime.datetime.now(),
    }

    import pydevd
    pydevd.settrace('host.docker.internal', port=3758, stdoutToServer=True, stderrToServer=True)

    try:
        send_mail(
            subject=_("New appeal through the contact form"),
            message=render_to_string("openassessmentblock/emails/oa_staff_return_assessment_email.html", email_params),
            from_email=from_email,
            recipient_list=[user_email],
            fail_silently=False
        )
    except SMTPException:
        log.warning("Failure sending contact form e-mail")
