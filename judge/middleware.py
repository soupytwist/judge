
class CheckAttempts:
    def process_request(self, request):
        if request.user.is_authenticated():
            attempts = request.user.attempts.filter(status=1).all()
            for attempt in attempts:
                if attempt.time_passed() >= attempt.problem.time_limit:
                    attempt.status = 3
                    attempt.reason = 3
                    attempt.save()
        return None
