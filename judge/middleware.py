from judge.models import Attempt

class CheckAttempts:
    def process_request(self, request):
        if request.user.is_authenticated():
            attempts = Attempt.objects.filter(status=Attempt.IN_PROGRESS).all()
            for attempt in attempts:
                if attempt.time_passed() >= attempt.problem.time_limit:
                    attempt.status = Attempt.INCORRECT
                    attempt.reason = Attempt.TIMEOUT
                    attempt.save()
        return None
