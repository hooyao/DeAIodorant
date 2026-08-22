"""Local authentication overrides for the human-review service."""

from django import forms
from users.forms import LoginForm


class PersistentLocalLoginForm(LoginForm):
    """Use a persistent cookie because embedded browsers discard session cookies."""

    persist_session = forms.BooleanField(
        widget=forms.CheckboxInput(), required=False, initial=True
    )

    def clean(self, *args, **kwargs):
        cleaned = super().clean(*args, **kwargs)
        if cleaned.get("user") is not None:
            cleaned["persist_session"] = True
        return cleaned
