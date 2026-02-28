"""
Review Manager - Wrong answer review and shuffled re-quiz.

Purpose: Load previously wrong answers, present them to the user for review,
         then re-quiz the user on those questions in shuffled order.
Inputs: Wrong answers from wrong_answers.json.
Outputs: Review session results (re-graded score on wrong questions).
Dependencies: quiz/grader.py, config.py.
"""

import random
from quiz.grader import load_wrong_answers, grade_answer, clear_wrong_answers
from quiz.question_generator import _shuffle_options


def get_review_questions() -> list:
    """
    Load wrong answers and convert them into re-quiz questions (shuffled).

    Returns:
        A shuffled list of question dicts ready for re-quizzing.
        Empty list if no wrong answers exist.
    """
    wrong = load_wrong_answers()
    if not wrong:
        print("No wrong answers to review.")
        return []

    # Deduplicate by question text (keep latest entry)
    seen = {}
    for entry in wrong:
        seen[entry["question"]] = entry
    unique = list(seen.values())

    # Convert wrong answer entries back to question format
    questions = []
    for entry in unique:
        q = {
            "question": entry["question"],
            "options": entry["options"],
            "answer": entry["correct_answer"],
            "source_text": entry.get("source_text", ""),
        }
        questions.append(q)

    random.shuffle(questions)
    return [_shuffle_options(q) for q in questions]


def run_review_session() -> dict:
    """
    Run an interactive review session on wrong answers via CLI.

    Returns:
        A dict with: score, total, percentage, still_wrong (list of questions
        the user got wrong again).
    """
    questions = get_review_questions()
    if not questions:
        return {"score": 0, "total": 0, "percentage": 0.0, "still_wrong": []}

    print(f"\n{'='*50}")
    print(f"  REVIEW MODE: {len(questions)} question(s) to review")
    print(f"{'='*50}\n")

    correct = 0
    still_wrong = []

    for i, q in enumerate(questions, 1):
        print(f"Question {i}/{len(questions)}: {q['question']}")
        for letter, text in q["options"].items():
            print(f"  {letter}) {text}")

        while True:
            answer = input("\nYour answer (A/B/C/D): ").strip().upper()
            if answer in ("A", "B", "C", "D"):
                break
            print("Please enter A, B, C, or D.")

        if grade_answer(q, answer):
            correct += 1
            print("Correct!\n")
        else:
            still_wrong.append(q)
            print(f"Wrong. The correct answer is: {q['answer']}) {q['options'][q['answer']]}")
            if q.get("source_text"):
                print(f"Source: {q['source_text']}")
            print()

    total = len(questions)
    percentage = correct / total if total > 0 else 0.0

    print(f"\nReview Score: {correct}/{total} ({percentage*100:.0f}%)")

    return {
        "score": correct,
        "total": total,
        "percentage": round(percentage, 2),
        "still_wrong": still_wrong,
    }


def has_wrong_answers() -> bool:
    """Check if there are any wrong answers available for review."""
    wrong = load_wrong_answers()
    return len(wrong) > 0


def get_wrong_count() -> int:
    """Return the number of unique wrong answers available for review."""
    wrong = load_wrong_answers()
    seen = set()
    for entry in wrong:
        seen.add(entry["question"])
    return len(seen)


if __name__ == "__main__":
    print(f"Wrong answers available: {has_wrong_answers()}")
    print(f"Unique wrong questions: {get_wrong_count()}")
    questions = get_review_questions()
    print(f"Review questions loaded: {len(questions)}")
    for q in questions:
        print(f"  - {q['question']} (answer: {q['answer']})")
