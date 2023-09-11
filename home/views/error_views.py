from django.shortcuts import render


def unauthenticated(request, exception):
    return render(
        request, "pages/error/unauthenticated.html", context={"exception": exception}
    )


def not_found(request):
    return render(request, "pages/error/not_found.html")
