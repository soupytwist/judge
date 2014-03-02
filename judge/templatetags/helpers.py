from django import template
from judge.models import Attempt

register = template.Library()

@register.assignment_tag(takes_context=True)
def problem_score(context, problem):
    request = context['request']
    att = request.user.attempts.filter(problem=problem).order_by("-score").first()
    return att.score if att is not None else -1

@register.filter()
def as_pct(val, maximum):
    return (float(val) / maximum) * 100.0
