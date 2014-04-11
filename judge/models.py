from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from judge import settings
from functools import partial
from datetime import datetime
import os
import random
import string

def get_upload_path(ft, instance, filename):
    if ft == "out":
        ext = ".out"
    else:
        try:
            ext = filename[filename.rindex('.'):]
        except ValueError:
            ext = ".src"

    part = instance.part
    problem = part.problem
    contest = problem.contest

    return os.path.join(settings.SUBMISSION_DIR,
            "%d-%s" % (contest.id, contest.slug), instance.owner.username,
            "%s_%s-%d%s" % (problem.slug, part.name, instance.testfileid, ext))

def get_problem_directory(instance, filename):
    contest = instance.contest
    return os.path.join(settings.SUBMISSION_DIR,
            "%d-%s" % (contest.id, contest.slug), instance.slug, filename)

class Contest(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField()
    begin_at = models.DateTimeField()
    end_at = models.DateTimeField()
    contestants = models.ManyToManyField(User, related_name="contests", blank=True)
    description = models.TextField()

    def get_active(self):
        now = datetime.now(self.begin_at.tzinfo)
        if self.end_at < now:
            return "Ended"
        elif self.begin_at < now:
            return "In Progress"
        else:
            return "Not Started"
    
    def has_begun(self):
        now = datetime.now(self.begin_at.tzinfo)
        return self.begin_at < now

    def has_ended(self):
        now = datetime.now(self.begin_at.tzinfo)
        return self.end_at < now
    
    def is_ongoing(self):
        now = datetime.now(self.begin_at.tzinfo)
        return self.begin_at < now and self.end_at > now

    def has_contestant(self, user):
        if not user.is_authenticated():
            return False
        return self.contestants.filter(id=user.id).exists()

    def get_score(self, user):
        return sum([problem.get_score(user) for problem in self.problems.all()], 0)

    def __str__(self):
        return "%s (%s)" % (self.name, self.get_active())

class Problem(models.Model):
    contest = models.ForeignKey(Contest, related_name="problems")
    name = models.CharField(max_length=256)
    order = models.CharField(max_length=2)
    time_limit = models.IntegerField()
    slug = models.SlugField()
    pdf = models.FileField(upload_to=get_problem_directory)
    sampleinput = models.FileField("Sample Input", upload_to=get_problem_directory)
    sampleoutput = models.FileField("Sample Output", upload_to=get_problem_directory)

    class Meta:
        ordering = ['order']

    def attempt_count(self):
        return self.attempts.count()

    def clarification_count(self):
        return self.clarifications.exclude(answer="").count()

    def __str__(self):
        return "%s. %s" % (self.order, self.name)

    def pdf_relative(self):
        return reverse('problem_pdf', kwargs={
                'contest': self.contest.slug,
                'slug': self.slug
            })

    def total_points(self):
        return self.parts.aggregate(total=models.Sum("points"))['total'] or 0

    def get_score(self, user):
        return sum([part.get_score(user) for part in self.parts.all()], 0)

    def get_next_part(self, user):
        for part in self.parts.all():
            if part.get_score(user) != part.points:
                return part
        return None

class ProblemPart(models.Model):
    problem = models.ForeignKey(Problem, related_name="parts")
    name = models.CharField(max_length=64)
    points = models.IntegerField()
    order = models.IntegerField()

    class Meta:
        ordering = ['order']

    def get_score(self, user):
        if self.attempts.filter(owner=user).count() == 0:
            return 0
        return self.attempts.filter(owner=user).aggregate(maxscore=models.Max("score"))['maxscore']

class Attempt(models.Model):
    IN_PROGRESS = 1
    CORRECT = 2
    INCORRECT = 3
    
    CHOICES_STATUS = (
        (IN_PROGRESS,   "Pending"),
        (CORRECT,       "Correct"),
        (INCORRECT,     "Incorrect"),
    )

    ACCEPTED = 1
    WRONG_ANSWER = 2
    TIMEOUT = 3
    BAD_SUBMISSION = 4
    SCORED_MANUALLY = 5

    CHOICES_REASON = (
        (ACCEPTED, "Accepted"),
        (WRONG_ANSWER, "Wrong Answer"),
        (TIMEOUT, "Time Limit Exceeded"),
        (BAD_SUBMISSION, "Bad Submission"),
        (SCORED_MANUALLY, "Scored Manually"),
    )

    owner = models.ForeignKey(User, related_name="attempts")
    part = models.ForeignKey(ProblemPart, related_name="attempts")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=CHOICES_STATUS, default=1)
    score = models.IntegerField(default=0)
    reason = models.IntegerField(choices=CHOICES_REASON, null=True)
    testfileid = models.IntegerField()
    outputfile = models.FileField("Ouptut File", upload_to=partial(get_upload_path, 'out'), null=True, blank=True)
    sourcefile = models.FileField("Source File", upload_to=partial(get_upload_path, 'src'), null=True, blank=True)
    randomness = models.CharField(max_length=16, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self):
        if self.testfileid is None:
            self.testfileid = Attempt.objects.filter(part=self.part).count()
        if not self.randomness:
            self.randomness = "".join(random.choice(string.ascii_letters+string.digits) for i in range(16))
        return super().save()

    def time_passed(self):
        return min(int((datetime.now(self.created_at.tzinfo) - self.created_at).total_seconds()), self.part.problem.time_limit)

    def get_inputfile_path(self):
        return os.path.join(settings.SECRET_DIR, "inputs",
                self.part.problem.slug, "%s-%d.in" % (self.part.name, self.testfileid))

    def get_outputfile_path(self):
        return os.path.join(settings.SECRET_DIR, "outputs",
                self.part.problem.slug, "%s-%d.out" % (self.part.name, self.testfileid))

    def is_in_progress(self):
        return self.status == 1

    def is_accepted(self):
        return self.status == 2

    def is_rejected(self):
        return self.status == 3

class Clarification(models.Model):
    owner = models.ForeignKey(User)
    problem = models.ForeignKey(Problem, related_name="clarifications")
    created_at = models.DateTimeField(auto_now_add=True)
    question = models.CharField(max_length=2048)
    answer = models.CharField(max_length=2048, blank=True)
