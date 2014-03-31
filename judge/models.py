from django.db import models
from django.contrib.auth.models import User
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

    return os.path.join(settings.SUBMISSION_DIR,
            "%d-%s" % (instance.problem.contest.id, instance.problem.contest.slug),
            instance.owner.username,
            "%s_%d%s" % (instance.problem.slug, instance.testfileid, ext))

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

    def __str__(self):
        return "%s (%s)" % (self.name, self.get_active())

class Problem(models.Model):
    contest = models.ForeignKey(Contest, related_name="problems")
    name = models.CharField(max_length=256)
    order = models.CharField(max_length=2)
    time_limit = models.IntegerField()
    slug = models.SlugField()
    pdf = models.FilePathField(path=settings.PROBLEM_DIR)
    max_score = models.IntegerField(default=100)

    class Meta:
        ordering = ['order']

    def attempt_count(self):
        return self.attempts.count()

    def __str__(self):
        return "%s. %s" % (self.order, self.name)

    def pdf_relative(self):
        return self.pdf[self.pdf.find("/problems/") + 1:]

    #def percent_correct(self):
    #    return self.attempt_set.

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

    CHOICES_REASON = (
        (ACCEPTED, "Accepted"),
        (WRONG_ANSWER, "Wrong Answer"),
        (TIMEOUT, "Time Limit Exceeded"),
        (BAD_SUBMISSION, "Bad Submission"),
    )

    owner = models.ForeignKey(User, related_name="attempts")
    problem = models.ForeignKey(Problem, related_name="attempts")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=CHOICES_STATUS, default=1)
    score = models.IntegerField()
    reason = models.IntegerField(choices=CHOICES_REASON, null=True)
    testfileid = models.IntegerField()
    outputfile = models.FileField("Ouptut File", upload_to=partial(get_upload_path, 'out'), null=True)
    sourcefile = models.FileField("Source File", upload_to=partial(get_upload_path, 'src'), null=True)
    randomness = models.CharField(max_length=16, blank=True)

    class Meta:
        ordering = ['-testfileid']

    def save(self):
        if self.testfileid is None:
            self.testfileid = Attempt.objects.filter(problem=self.problem).count()
        if not self.randomness:
            self.randomness = "".join(random.choice(string.ascii_letters+string.digits) for i in range(16))
        return super().save()

    def time_passed(self):
        return min(int((datetime.now(self.created_at.tzinfo) - self.created_at).total_seconds()), self.problem.time_limit)

    def get_inputfile_path(self):
        return os.path.join(settings.PROJECT_DIR, "secret", "inputs",
                self.problem.slug, str(self.testfileid) + ".in")

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
