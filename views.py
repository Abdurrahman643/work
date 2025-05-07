from django.shortcuts import render
# from .models import Student, Enrollment, Payment, Testimonial


def homepage(request):
    #return HttpResponse("hello world")
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')
