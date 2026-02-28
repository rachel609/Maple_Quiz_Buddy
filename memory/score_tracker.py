"""
Score Tracker - Multi-attempt score tracking and progress analysis.

Purpose: Record quiz scores across multiple attempts and provide progress summaries.
Inputs: Score data from the grader after each quiz attempt.
Outputs: Score history, progress analysis, and trend reports.
Dependencies: config.py.

score_log.json format:
    {"attempt": 1, "date": "YYYY-MM-DD", "score": 15, "total": 20, "percentage": 0.75}
"""

import json
import os
from datetime import date
import config


def save_score(score: int, total: int) -> dict:
    """
    Save a quiz score to score_log.json.

    Args:
        score: Number of correct answers.
        total: Total number of questions.

    Returns:
        The score entry dict that was saved.
    """
    history = load_score_history()
    attempt = len(history) + 1
    percentage = round(score / total, 2) if total > 0 else 0.0

    entry = {
        "attempt": attempt,
        "date": str(date.today()),
        "score": score,
        "total": total,
        "percentage": percentage,
    }

    history.append(entry)
    _write_history(history)
    print(f"Score saved: Attempt #{attempt} — {score}/{total} ({percentage*100:.0f}%)")
    return entry


def load_score_history() -> list:
    """Load all score entries from score_log.json."""
    path = config.SCORE_LOG_PATH
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _write_history(history: list):
    """Write score history to score_log.json."""
    path = config.SCORE_LOG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def get_progress_summary() -> str:
    """
    Generate a human-readable progress summary across all attempts.

    Returns:
        A formatted string with score history and trends.
    """
    history = load_score_history()

    if not history:
        return "No quiz attempts recorded yet."

    lines = []
    lines.append(f"\n{'='*50}")
    lines.append("  SCORE HISTORY")
    lines.append(f"{'='*50}")

    for entry in history:
        pct = entry["percentage"] * 100
        status = "PASS" if entry["percentage"] >= config.PASSING_SCORE else "FAIL"
        lines.append(
            f"  Attempt #{entry['attempt']} ({entry['date']}): "
            f"{entry['score']}/{entry['total']} ({pct:.0f}%) [{status}]"
        )

    # Stats
    scores = [e["percentage"] for e in history]
    best = max(scores)
    worst = min(scores)
    avg = sum(scores) / len(scores)
    total_attempts = len(history)
    passes = sum(1 for s in scores if s >= config.PASSING_SCORE)

    lines.append(f"\n{'='*50}")
    lines.append("  SUMMARY")
    lines.append(f"{'='*50}")
    lines.append(f"  Total attempts: {total_attempts}")
    lines.append(f"  Passed: {passes}/{total_attempts}")
    lines.append(f"  Best score: {best*100:.0f}%")
    lines.append(f"  Worst score: {worst*100:.0f}%")
    lines.append(f"  Average: {avg*100:.0f}%")

    # Trend
    if len(scores) >= 2:
        if scores[-1] > scores[-2]:
            lines.append("  Trend: Improving! Keep it up!")
        elif scores[-1] < scores[-2]:
            lines.append("  Trend: Score dropped. Review your weak areas.")
        else:
            lines.append("  Trend: Steady. Push for improvement!")

    lines.append(f"{'='*50}\n")
    return "\n".join(lines)


def get_attempt_count() -> int:
    """Return the number of quiz attempts so far."""
    return len(load_score_history())


def clear_score_history():
    """Reset score_log.json to empty."""
    _write_history([])
    print("Score history cleared.")


if __name__ == "__main__":
    # Self-test: save a few scores and print summary
    clear_score_history()

    save_score(12, 20)
    save_score(15, 20)
    save_score(18, 20)

    print(get_progress_summary())
    print(f"Total attempts: {get_attempt_count()}")
