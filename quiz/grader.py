"""
Grader - Grade quiz answers and log wrong answers to file.

Purpose: Compare user answers to correct answers, calculate scores,
         and persist wrong answers for later review.
Inputs: A list of question dicts and the user's answers.
Outputs: Score summary dict and updated wrong_answers.json.
Dependencies: config.py.
"""

import json
import os
from datetime import date
import config


def grade_answer(question: dict, user_answer: str) -> bool:
    """
    Check if a single answer is correct.

    Args:
        question: A question dict with key 'answer' (e.g. 'B').
        user_answer: The user's answer letter (e.g. 'A').

    Returns:
        True if correct, False otherwise.
    """
    return user_answer.upper().strip() == question["answer"].upper().strip()


def grade_quiz(questions: list, user_answers: list) -> dict:
    """
    Grade a full quiz and log wrong answers.

    Args:
        questions: List of question dicts (from question_generator).
        user_answers: List of answer strings in the same order as questions.

    Returns:
        A dict with keys: score, total, percentage, passed, wrong_questions.
    """
    if len(questions) != len(user_answers):
        raise ValueError(
            f"Mismatch: {len(questions)} questions but {len(user_answers)} answers."
        )

    correct = 0
    wrong_questions = []

    for q, ans in zip(questions, user_answers):
        if grade_answer(q, ans):
            correct += 1
        else:
            wrong_entry = {
                "question": q["question"],
                "options": q["options"],
                "user_answer": ans.upper().strip(),
                "correct_answer": q["answer"],
                "source_text": q.get("source_text", ""),
                "date": str(date.today()),
            }
            wrong_questions.append(wrong_entry)

    total = len(questions)
    percentage = correct / total if total > 0 else 0.0

    result = {
        "score": correct,
        "total": total,
        "percentage": round(percentage, 2),
        "passed": percentage >= config.PASSING_SCORE,
        "wrong_questions": wrong_questions,
    }

    if wrong_questions:
        _save_wrong_answers(wrong_questions)

    return result


def _save_wrong_answers(wrong_questions: list):
    """Append wrong answers to wrong_answers.json."""
    path = config.WRONG_ANSWERS_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    existing = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []

    existing.extend(wrong_questions)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(wrong_questions)} wrong answer(s) to {path}")


def load_wrong_answers() -> list:
    """Load all wrong answers from wrong_answers.json."""
    path = config.WRONG_ANSWERS_PATH
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def clear_wrong_answers():
    """Reset wrong_answers.json to empty."""
    path = config.WRONG_ANSWERS_PATH
    with open(path, "w", encoding="utf-8") as f:
        json.dump([], f)
    print("Wrong answers cleared.")


if __name__ == "__main__":
    # Quick self-test
    test_questions = [
        {"question": "Capital of Canada?", "options": {"A": "Toronto", "B": "Ottawa", "C": "Vancouver", "D": "Montreal"}, "answer": "B", "source_text": "Ottawa is the capital."},
        {"question": "Official languages?", "options": {"A": "English", "B": "French", "C": "English and French", "D": "Spanish"}, "answer": "C", "source_text": "English and French."},
        {"question": "First PM?", "options": {"A": "Laurier", "B": "Macdonald", "C": "Trudeau", "D": "Mackenzie"}, "answer": "B", "source_text": "Sir John A. Macdonald."},
    ]
    test_answers = ["B", "A", "B"]  # 2 correct, 1 wrong

    result = grade_quiz(test_questions, test_answers)
    print(f"\nScore: {result['score']}/{result['total']} ({result['percentage']*100}%)")
    print(f"Passed: {result['passed']}")
    print(f"Wrong: {len(result['wrong_questions'])}")

    for w in result["wrong_questions"]:
        print(f"  - {w['question']}: answered {w['user_answer']}, correct {w['correct_answer']}")
