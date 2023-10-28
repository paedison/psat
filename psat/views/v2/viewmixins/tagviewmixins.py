from psat.forms import TagForm
from psat.models import Tag
from reference.models import PsatProblem


class TagViewMixIn:
    """Setting mixin for Tag views."""
    menu = 'tag'
    kwargs: dict
    request: any

    object: Tag
    model = Tag
    form_class = TagForm
    context_object_name = 'my_tag'
    lookup_field = 'id'
    lookup_url_kwarg = 'tag_id'

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    @property
    def my_tag_id(self) -> int | None:
        """Get my_tag_id in case of tag_container, tag_add, tag_delete."""
        tag_id = self.kwargs.get('tag_id')
        return int(tag_id) if tag_id else None

    @property
    def my_tag(self):
        """Return my_tag field in the ProblemTag model if my_tag_id exists."""
        return Tag.objects.get(id=self.my_tag_id) if self.my_tag_id else None

    @property
    def problem_id(self) -> int | None:
        """Get problem_id in case of tag_create."""
        problem_id = self.kwargs.get('problem_id')
        return int(problem_id) if problem_id else None

    @property
    def problem(self):
        """Return problem in the Problem model if problem_id exists."""
        if self.problem_id:
            return PsatProblem.objects.get(id=self.problem_id)
        if self.my_tag_id:
            return PsatProblem.objects.get(id=self.my_tag.problem_id)

    @property
    def my_tag_list(self) -> list | None:
        """Return my_tag_list if my_tag is not none."""
        if self.my_tag is not None:
            tag_names = list(self.my_tag.tags.names())
            tag_names.sort()
            return tag_names
        return None

    @property
    def all_tags(self) -> list:
        """Return all_tags corresponding to the targeted problem."""
        problem_tags = Tag.objects.filter(problem=self.problem)
        tags_list = []
        if problem_tags:
            for problem_tag in problem_tags:
                tags_list.extend(problem_tag.tags.names())
        all_tags_list = list(set(tags_list))
        all_tags_list.sort()
        return all_tags_list
