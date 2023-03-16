from django.shortcuts import redirect, render
from .forms import RegisterForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.generic import CreateView
from django.urls import reverse_lazy
import git
from django.contrib.auth import logout

# Create your views here.


@csrf_exempt
def git_update(request):
    if request.method != "POST":
        return HttpResponse("Couldn't update the code on PythonAnywhere")
    '''
        pass the path of the diectory where your project will be 
        stored on PythonAnywhere in the git.Repo() as parameter.
        Here the name of my directory is "test.pythonanywhere.com"
        '''
    repo = git.Repo('/home/iol/IOL')
    origin = repo.remotes.origin
    origin.pull()
    return HttpResponse("Updated code on PythonAnywhere")

class SignUpView(CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy("login")
    template_name = "base/signup.html"


def logout_view(request):
    logout(request)
    return redirect('project_list')
