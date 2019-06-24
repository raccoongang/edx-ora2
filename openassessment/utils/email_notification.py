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


def send_notification_email(user_email, submission, action_name, comment):
    """
    Util function that send notification email to learner about status his/her assessment

    Email sends after staff `cancel_submission`, `return_submission` and `done_submission` actions.
    :param user_email: string User email
    :param submission: object submission of user assessment
    :param action_name: string Name that specify action of email sending message
    :param comment: string Staff comment about assessment
    """
    from_email = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    lms_root_url = getattr(settings, 'LMS_ROOT_URL')

    path = get_redirect_url(
        CourseKey.from_string(submission['student_item']['course_id']),
        UsageKey.from_string(submission['student_item']['item_id'])
    )

    email_params = {
        'url': lms_root_url + path,
        'datetime': datetime.datetime.now(),
        'comment': comment,
    }

    email_action_dict = {
        "done": {
            "subject": _("Assessment is done"),
            "template": "openassessmentblock/emails/oa_staff_done_assessment_email.txt"
        },
        "return": {
            "subject": _("Assessment is returned"),
            "template": "openassessmentblock/emails/oa_staff_return_assessment_email.txt"
        },
        "cancel": {
            "subject": _("Assessment is canceled"),
            "template": "openassessmentblock/emails/oa_staff_cancel_assessment_email.txt"
        }
    }

    try:
        send_mail(
            subject=email_action_dict.get(action_name).get("subject"),
            message=render_to_string(email_action_dict.get(action_name).get("template"), email_params),
            from_email=from_email,
            recipient_list=[user_email],
            fail_silently=False
        )
    except SMTPException:
        log.exception("Failure sending ORA staff response form e-mail")
