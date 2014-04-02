from judge.models import Attempt

def score_line(mine, theirs):
    return theirs.split() == mine.split()

def filter_lines(lines):
    return [line for line in lines if line]

def score(attempt):
    with open(attempt.outputfile.path, "r") as answer:
        with open(attempt.get_inputfile_path(), "r") as oracle:
            answerlines = filter_lines(answer.readlines())
            oraclelines = filter_lines(oracle.readlines())
            
            if len(answerlines) != len(oraclelines):
                attempt.score = 0
                attempt.status = Attempt.INCORRECT
                attempt.reason = Attempt.BAD_SUBMISSION
                attempt.save()
                return
            
            if all(score_line(mine, theirs) for mine, theirs in zip(oraclelines, answerlines)):
                attempt.score = attempt.part.points
                attempt.status = Attempt.CORRECT
                attempt.reason = Attempt.ACCEPTED
                attempt.save()
                return

    attempt.score = 0
    attempt.status = Attempt.INCORRECT
    attempt.reason = Attempt.WRONG_ANSWER
    attempt.save()
    return
