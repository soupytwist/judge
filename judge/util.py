
def score(attempt):
    correct = 0
    missed = 0

    with open(attempt.outputfile.path, "r") as answer:
        with open(attempt.get_inputfile_path(), "r") as oracle:
            answerlines = answer.readlines()
            oraclelines = oracle.readlines()
            ct = len(oraclelines)

            if len(answerlines) != ct:
                attempt.status = 3
                attempt.reason = 4
                attempt.score = 0
                attempt.save()
                return
            
            for theirs, mine in zip(answerlines, oraclelines):
                if theirs.split() == mine.split():
                    correct += 1
                else:
                    missed += 1

            attempt.score = int((float(correct)/ct) * attempt.problem.max_score)
            attempt.status = 2 if missed == 0 else 3
            attempt.reason = 1 if missed == 0 else 2
            attempt.save()
