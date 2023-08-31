from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.shortcuts import redirect
from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(AuthenticationForm):
    username = UsernameField(
        label=_(""),
        widget=forms.TextInput(
            attrs={"placeholder": "Username", "class": "form-control"}
        ),
    )
    password = forms.CharField(
        label=_(""),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "autocomplete": "current-password",
                "class": "form-control",
            }
        ),
    )


class UserLoginView(auth_views.LoginView):
    template_name = "pages/login.html"
    form_class = LoginForm
    success_url = "/"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/")  # Redirect to index if user is authenticated
        return super().get(request, *args, **kwargs)


def user_logout_view(request):
    logout(request)
    return redirect("/login/")
