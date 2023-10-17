from ..utils.decorators import is_authenticated
from django.shortcuts import render
from api.models.kubecost import KubecostReport
from home.models.tech_family import TechFamily


@is_authenticated
def kubecost(request):
    input_date = request.GET.get('date')
    input_period = request.GET.get('period')
    input_tf = request.GET.get('tech_family')

    if input_date == None or input_period == None or input_tf == None:
        services = []
        date_range = None
    else:
        report = KubecostReport.report(input_date, input_period)
        services = report[input_tf]['data']['services']
        date_range = report[input_tf]['data']['date']

    tech_family = TechFamily.objects.all()

    data = {
        'tech_family': tech_family,
        'services': services,
        'date_range': date_range,
        'input_date': input_date,
        'input_period': input_period,
        'input_tf': input_tf,
    }

    return render(request, 'pages/kubecost.html', data)

