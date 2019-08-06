"""
Models for managing staff assessments.
"""
from datetime import timedelta
import logging

from django.db import DatabaseError, models
from django.utils.timezone import now

from openassessment.assessment.errors import StaffAssessmentInternalError

logger = logging.getLogger("openassessment.assessment.api.staff")


class StaffWorkflow(models.Model):
    """
    Internal Model for tracking Staff Assessment Workflow

    This model can be used to determine the following information required
    throughout the Staff Assessment Workflow:

    1) Get next submission that requires assessment.
    2) Does a submission have a staff assessment?
    3) Does this staff member already have a submission open for assessment?
    4) Close open assessments when completed.

    """
    # Amount of time before a lease on a submission expires
    TIME_LIMIT = timedelta(hours=8)

    scorer_id = models.CharField(max_length=40, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)
    item_id = models.CharField(max_length=128, db_index=True)
    submission_uuid = models.CharField(max_length=128, db_index=True, unique=True)
    created_at = models.DateTimeField(default=now, db_index=True)
    grading_completed_at = models.DateTimeField(null=True, db_index=True)
    grading_started_at = models.DateTimeField(null=True, db_index=True)
    cancelled_at = models.DateTimeField(null=True, db_index=True)
    assessment = models.CharField(max_length=128, db_index=True, null=True)
    returned_at = models.DateTimeField(null=True, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]
        app_label = "assessment"

    @property
    def is_cancelled(self):
        """
        Check if the workflow is cancelled.

        Returns:
            True/False
        """
        return bool(self.cancelled_at)

    @classmethod
    def get_workflow_statistics(cls, course_id, item_id):
        """
        Returns the number of graded, ungraded, and in-progress submissions for staff grading.

        Args:
            course_id (str): The course that this problem belongs to
            item_id (str): The student_item (problem) that we want to know statistics about.

        Returns:
            dict: a dictionary that contains the following keys: 'graded', 'ungraded', and 'in-progress'
        """
        timeout = (now() - cls.TIME_LIMIT).strftime("%Y-%m-%d %H:%M:%S")
        ungraded = cls.objects.filter(
            models.Q(grading_started_at=None) | models.Q(grading_started_at__lte=timeout),
            course_id=course_id, item_id=item_id, grading_completed_at=None, cancelled_at=None
        ).count()

        in_progress = cls.objects.filter(
            course_id=course_id, item_id=item_id, grading_completed_at=None, cancelled_at=None,
            grading_started_at__gt=timeout
        ).count()

        graded = cls.objects.filter(
            course_id=course_id, item_id=item_id, cancelled_at=None
        ).exclude(grading_completed_at=None).count()

        return {'ungraded': ungraded, 'in-progress': in_progress, 'graded': graded}

    @classmethod
    def get_submissions_for_review(cls, course_id, item_id):
        """
        Find all submissions for staff assessment.

        Args:
            course_id (str): The course ID for filtering submissions for current course.
            item_id (str): The student_item that we would like to retrieve submissions for.

        Returns:
            QuerySet object: QuerySet with the list of submission_uuid's for review.

        Raises:
            StaffAssessmentInternalError: Raised when there is an error retrieving
                the workflows for this request.

        """

        try:
            return StaffWorkflow.objects.filter(
                course_id=course_id,
                item_id=item_id,
                grading_completed_at=None,
                cancelled_at=None,
                returned_at=None,
            ).values_list('submission_uuid', flat=True)

        except DatabaseError:
            error_message = (
                u"An internal error occurred while retrieving a submissions for staff grading"
            )
            logger.exception(error_message)
            raise StaffAssessmentInternalError(error_message)

    def close_active_assessment(self, assessment, scorer_id):
        """
        Assign assessment to workflow, and mark the grading as complete.
        """
        self.assessment = assessment.id
        self.scorer_id = scorer_id
        self.grading_completed_at = now()
        self.save()
