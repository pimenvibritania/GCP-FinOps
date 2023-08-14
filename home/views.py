from django.shortcuts import render, redirect
from theme_material_kit.forms import LoginForm
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views

def index(request): 
    return render(request, 'pages/index.html')

class UserLoginView(auth_views.LoginView):
    template_name = 'pages/login.html'
    form_class = LoginForm
    success_url = '/'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')  # Redirect to index if user is authenticated
        return super().get(request, *args, **kwargs)

def user_logout_view(request):
    logout(request)
    return redirect('/login/')
