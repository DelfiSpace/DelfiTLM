from django.shortcuts import render

def home(request):
    """render index.html page"""
    print("got here")
    ren = render(request, "home/index.html")
    return ren