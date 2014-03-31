from django import template
from judge.models import Attempt

register = template.Library()

@register.assignment_tag(takes_context=True)
def problem_score(context, problem):
    request = context['request']
    if not problem.contest.has_contestant(request.user):
        return -1
    att = request.user.attempts.filter(problem=problem).order_by("-score").first()
    return att.score if att is not None else -1

@register.assignment_tag(takes_context=True)
def user_is_contestant(context, contest):
    request = context['request']
    return contest.has_contestant(request.user)

@register.filter()
def as_pct(val, maximum):
    return (float(val) / maximum) * 100.0
