from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic import DetailView, ListView, CreateView, UpdateView
import django.contrib.messages
from judge import models
from judge.util import score

class ContestView(DetailView):
    model = models.Contest
    template_name = "contest.html"
    context_object_name = 'contest'

class ProblemView(DetailView):
    model = models.Problem
    template_name = "problem.html"
    context_object_name = 'problem'

def start_submit(request, **kwargs):
    try:
        problem = models.Problem.objects.filter(slug=kwargs['slug'], contest__slug=kwargs['contest']).get()
        user = request.user

        att = user.attempts.filter(problem=problem, status=1).first()
        if att is None:
            att = models.Attempt(problem=problem, owner=user, status=1, score=0)
            att.save()
        
        kwargs['attempt_pk'] = att.id
        return redirect(reverse("problem_submit", kwargs=kwargs))

    except models.Problem.DoesNotExist:
        return redirect(reverse("problem_home", kwargs=kwargs))

class SubmitView(UpdateView):
    model = models.Attempt
    template_name = "submit.html"
    fields = ['outputfile', 'sourcefile']
    pk_url_kwarg = "attempt_pk"
    context_object_name = "attempt"
    success_url = "/"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['problem'] = self.object.problem
        return data

    def form_valid(self, form):
        response = super().form_valid(form)
        score(self.object)
        print("Found the score to be %d" % (self.object.score))
        return response

def download_inputfile(request, **kwargs):
    attempt = models.Attempt.objects.get(pk=kwargs['attempt_pk'])
    path = attempt.get_inputfile_path()

    if not request.user.is_authenticated() or attempt.owner.id != request.user.id:
        return HttpResponse("You are not authorized to view this.", status=401)

    with open(path, "r") as f:
        content = f.read()
        resp = HttpResponse(content, content_type="text/plain")
        resp['Content-Length'] = len(content)
        resp['Content-Disposition'] = 'attachment; filename="input.txt"'
        return resp

class ProblemSubmissions(DetailView):
    model = models.Problem
    template_name = "submissions.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        myattempts = self.request.user.attempts.filter(problem=self.object).all()
        ctxt['attempts'] = myattempts
        return ctxt
