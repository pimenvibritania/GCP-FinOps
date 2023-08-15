from ..utils.decorators import is_authenticated
from django.shortcuts import render

@is_authenticated
def index(request):
    
    return render(request, 'pages/dashboard.html')
