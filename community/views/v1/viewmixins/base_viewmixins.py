from reference import models as reference_models
from community import forms as community_forms
from community import models as community_models


class CommunityModelVariableSet:
    exam_model = reference_models.Exam
    problem_model = reference_models.PsatProblem
    subject_model = reference_models.Subject

    category_model = community_models.Category
    post_model = community_models.Post
    comment_model = community_models.Comment

    post_form = community_forms.PostForm
