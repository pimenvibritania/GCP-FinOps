from ..utils.decorators import is_authenticated
from django.shortcuts import render

@is_authenticated
def tech_family(request):
    return render(request, 'pages/tech_family.html')
