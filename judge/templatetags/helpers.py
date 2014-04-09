from django import template
from judge.models import Attempt

register = template.Library()

@register.assignment_tag(takes_context=True)
def problem_score(context, problem):
    request = context['request']
    if not problem.contest.has_contestant(request.user):
        return -1
    return problem.get_score(request.user)

@register.assignment_tag(takes_context=True)
def contest_score(context, contest):
    request = context['request']
    if not contest.has_contestant(request.user):
        return 0
    return contest.get_score(request.user)

@register.assignment_tag(takes_context=True)
def user_is_contestant(context, contest):
    request = context['request']
    print(contest)
    return contest.has_contestant(request.user)

@register.assignment_tag(takes_context=True)
def problem_next_part(context, problem):
    request = context['request']
    return problem.get_next_part(request.user)

@register.filter()
def as_pct(val, maximum):
    return (float(val) / maximum) * 100.0
