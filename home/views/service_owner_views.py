from home.utils.decorators import is_authenticated
from django.shortcuts import render
from home.models.tech_family import TechFamily

@is_authenticated
def service_owner(request):
    tech_family = TechFamily.objects.all()
    return render(request, 'pages/service_owner.html', {'tech_family': tech_family})
