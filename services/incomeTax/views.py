
from django.http import HttpResponse


def sample_view(request):
    return HttpResponse("This is a sample response.")
