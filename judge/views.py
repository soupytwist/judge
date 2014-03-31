from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound
from django.views.generic import DetailView, ListView, CreateView, UpdateView
import django.contrib.messages
from django.contrib.messages.views import SuccessMessageMixin
from judge import models
from judge.util import score
from judge.forms import ClarificationForm
from sendfile import sendfile

class ContestView(DetailView):
    model = models.Contest
    template_name = "contest.html"
    context_object_name = 'contest'

class ProblemView(DetailView):
    model = models.Problem
    template_name = "problem.html"

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

def download_inputfile(request, randomness=None, **kwargs):
    attempt = models.Attempt.objects.get(pk=kwargs['attempt_pk'])
    path = attempt.get_inputfile_path()

    if randomness != attempt.randomness:
        return HttpResponseNotFound("404 Not Found")

    return sendfile(request, path, attachment=True, attachment_filename="input.txt")

class ProblemSubmissions(DetailView):
    model = models.Problem
    template_name = "submissions.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        myattempts = self.request.user.attempts.filter(problem=self.object).all()
        ctxt['attempts'] = myattempts
        return ctxt

class ProblemClarifications(DetailView):
    model = models.Problem
    template_name = "clarifications.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        clarifications = self.object.clarifications.all()
        ctxt['clarifications'] = clarifications
        return ctxt

class ProblemAskClarification(SuccessMessageMixin, CreateView):
    model = models.Clarification
    template_name = "clarification_ask.html"
    success_message = "Your question has been submitted. Please check back later for a reply."
    problem = None
    asker = None

    def dispatch(self, request, *args, **kwargs):
        self.problem = get_object_or_404(models.Problem, contest__slug=kwargs['contest'], slug=kwargs['slug'])
        self.asker = request.user
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class):
        kwargs = super().get_form_kwargs()
        return ClarificationForm(asker=self.asker, problem=self.problem, **kwargs)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['problem'] = self.problem
        return ctxt

    def get_success_url(self):
        return reverse('problem_home', kwargs={
            'contest': self.problem.contest.slug,
            'slug': self.problem.slug,
        })

class AdminSubmissionList(ListView):
    model = models.Attempt
    template_name = "admin_submissions.html"
    context_object_name = 'attempts'
    contest = None

    def dispatch(self, *args, **kwargs):
        self.contest = get_object_or_404(models.Contest, slug=kwargs['contest'])
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(problem__contest=self.contest)
    
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['contest'] = self.contest
        return ctxt

class AdminAttemptDetail(DetailView):
    model = models.Attempt
    pk_url_kwarg = 'attempt_pk'
    template_name = "admin_attempt_detail.html"
    context_object_name = 'attempt'
    contest = None

    def dispatch(self, *args, **kwargs):
        self.contest = get_object_or_404(models.Contest, slug=kwargs['contest'])
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['contest'] = self.contest
        ctxt['problem'] = self.object.problem
        return ctxt
