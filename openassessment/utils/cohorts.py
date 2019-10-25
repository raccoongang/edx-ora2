from opaque_keys.edx.keys import CourseKey
from submissions.models import Submission

from lms.djangoapps.instructor.models import CohortAssigment
from openassessment.workflow.models import AssessmentWorkflow
from openedx.core.djangoapps.course_groups.models import CohortMembership


def get_assessments_by_cohorts(course_id, statuses, selected_cohort, user):
    """
    Get a queryset of assessments.

    Get a queryset of all the assessments depends on either selected cohort or
    user's cohorts where he is assigned as a leader in the given course.
    If selected cohort is not given or requested user does not have any cohorts,
    then returns all assessments in the given course.

    Arguments:
        course_id (string): the course ID for which cohorts should be returned,
        statuses (list): existing assessments statuses,
        selected_cohort (string): cohort ID that is chosen by user,
        user (User): requested user;

    Returns:
        A queryset of AssessmentWorkflow objects.
    """

    assessments = AssessmentWorkflow.objects.filter(course_id=course_id, status__in=statuses)

    is_cohort_related = selected_cohort or CohortAssigment.objects.has_cohorts(user)

    if is_cohort_related:
        desired_cohorts = (
            [selected_cohort]
            if selected_cohort
            else CohortAssigment.objects.filter(user=user).values_list('cohort__id', flat=True)
        )
        anonymous_user_ids = CohortMembership.objects.filter(
            course_id=CourseKey.from_string(course_id), course_user_group__id__in=desired_cohorts
        ).values('user__anonymoususerid__anonymous_user_id')
        relevant_submissions_uuid = Submission.objects.filter(
            student_item__student_id__in=anonymous_user_ids
        ).values('uuid')
        relevant_submissions_uuid_list = [str(uuid['uuid']) for uuid in relevant_submissions_uuid]
        assessments = assessments.filter(submission_uuid__in=relevant_submissions_uuid_list)

    return assessments
