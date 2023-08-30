from ..utils.decorators import is_authenticated
from django.shortcuts import render
from home.models.services import Services
from home.models.tech_family import TechFamily
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db import IntegrityError

@is_authenticated
def service_owner(request):
    tech_family = TechFamily.objects.all()
    return render(request, 'pages/service_owner.html', {'tech_family': tech_family})

@is_authenticated
def service_owner_add(request):
    if request.method == "POST":
        service = Services()
        service.name = request.POST.get('service_name')
        service.service_type = request.POST.get('service_type')
        service.project = request.POST.get('project')
        service.tech_family = TechFamily.objects.get(name = request.POST.get('tech_family'))
        try:
            service.save()
            messages.success(request, f"Service {request.POST.get('service_name')} added successfully !")
            return HttpResponseRedirect("/service-owner")
        except IntegrityError as e:
            messages.error(request, f"Duplicate entry for {request.POST.get('service_name')}")
            return HttpResponseRedirect("/service-owner")
    else:
        return HttpResponseRedirect("/service-owner")

@is_authenticated
def service_owner_detail(request, service_id):
    service = Services.objects.get(id = service_id)
    if service != None:
        return render(request, "pages/service_owner_edit.html", {'service': service})

@is_authenticated
def service_owner_edit(request):
    if request.method == "POST":
        service = Services.objects.get(id = request.POST.get('service_id'))
        if service != None:
            print(f"service_id = {request.POST.get('service_id')}")
            print(f"service_name = {request.POST.get('service_name')}")
            print(f"service_type = {request.POST.get('service_type')}")
            print(f"project = {request.POST.get('project')}")
            print(f"tech_family = {request.POST.get('tech_family')}")

            service.name = request.POST.get('service_name')
            service.service_type = request.POST.get('service_type')
            service.project = request.POST.get('project')
            service.tech_family = TechFamily.objects.get(name = request.POST.get('tech_family'))
            try:
                service.save()
                messages.success(request, f"Service {request.POST.get('service_name')} edited successfully !")
                return HttpResponseRedirect("/service-owner")
            except IntegrityError as e:
                messages.error(request, f"Duplicate entry for {request.POST.get('service_name')}")
                return HttpResponseRedirect("/service-owner")
    else:
        return HttpResponseRedirect("/service-owner")

@is_authenticated
def service_owner_delete(request):
    if request.method == "POST":
        service = Services.objects.get(id = request.POST.get('service_id'))
        if service != None:
            service.delete()
            messages.success(request, "Service deleted successfully !")
            return HttpResponseRedirect("/service-owner")
    else:
        return HttpResponseRedirect("/service-owner")

