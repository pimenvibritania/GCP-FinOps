from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied
from core import settings


class CustomGoogleOAuth2Adapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user_email = str(sociallogin.email_addresses[0])
        allowed_domains = settings.OAUTH_EMAIL_WHITELIST

        if not any(user_email.endswith(domain) for domain in allowed_domains):
            raise OAuth2Error("Invalid Email Domain")

    def authentication_error(
        self,
        request,
        provider_id,
        error=None,
        exception=None,
        extra_context=None,
    ):
        """
        Invoked when there is an error in the authentication cycle. In this
        case, pre_social_login will not be reached.

        You can use this hook to intervene, e.g. redirect to an
        educational flow by raising an ImmediateHttpResponse.
        """

        raise PermissionDenied(exception)
