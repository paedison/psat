from ckeditor.fields import RichTextField, RichTextFormField
from ckeditor.widgets import CKEditorWidget


class CustomCKEditorWidget(CKEditorWidget):
    media = None


class CustomRichTextFormField(RichTextFormField):
    widget = CustomCKEditorWidget


class CustomRichTextField(RichTextField):
    def formfield(self, **kwargs):
        defaults = {'form_class': CustomRichTextFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)

