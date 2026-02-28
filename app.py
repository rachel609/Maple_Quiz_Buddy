"""
Maple Quiz Buddy - Main Entry Point

Purpose: Orchestrate the full Canadian citizenship quiz flow:
         onboarding -> RAG setup -> quiz -> grading -> review -> score history.
Inputs: User interaction via CLI.
Outputs: Quiz results, feedback, score history.
Dependencies: All project modules (config, personality, rag, quiz, memory).
"""

import config
from personality.style_selector import run_onboarding
from personality.buddy_prompts import generate_system_prompt, get_feedback_prompt
from rag.vector_store import load_vector_store
from quiz.question_generator import generate_questions
from quiz.grader import grade_quiz, clear_wrong_answers
from quiz.review_manager import run_review_session, has_wrong_answers, get_wrong_count
from memory.score_tracker import save_score, get_progress_summary, get_attempt_count


def _get_llm_feedback(system_prompt: str, feedback_prompt: str) -> str:
    """
    Get personality-based feedback from the LLM.
    In sandbox mode, returns a simple placeholder message.
    """
    if config.is_sandbox():
        return ""

    try:
        from langchain_xai import ChatXAI
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{feedback}"),
        ])
        llm = ChatXAI(model=config.GROK_MODEL, api_key=config.XAI_API_KEY)
        chain = prompt | llm
        response = chain.invoke({"feedback": feedback_prompt})
        return response.content
    except Exception as e:
        print(f"[Warning] Could not get LLM feedback: {e}")
        return ""


def _run_quiz_round(system_prompt: str, style: str, language: str) -> dict:
    """Run a single quiz round: generate questions, collect answers, grade."""
    attempt = get_attempt_count() + 1
    print(f"\n{'='*50}")
    print(f"  QUIZ ATTEMPT #{attempt}")
    print(f"  {config.QUESTIONS_PER_QUIZ} questions — 75% to pass")
    print(f"{'='*50}\n")

    # Generate questions
    questions = generate_questions(
        num_questions=config.QUESTIONS_PER_QUIZ,
        system_prompt=system_prompt,
    )

    if not questions:
        print("Error: Could not generate questions. Please try again.")
        return None

    # Collect answers one at a time
    user_answers = []
    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i}/{len(questions)}: {q['question']}")
        for letter, text in q["options"].items():
            print(f"  {letter}) {text}")

        while True:
            answer = input("\nYour answer (A/B/C/D): ").strip().upper()
            if answer in ("A", "B", "C", "D"):
                break
            print("Please enter A, B, C, or D.")

        user_answers.append(answer)

        # Immediate feedback per question
        is_correct = answer == q["answer"]
        if config.is_sandbox():
            if is_correct:
                print("-> Correct!")
            else:
                print(f"-> Wrong. The correct answer is: {q['answer']}) {q['options'][q['answer']]}")
        else:
            scenario = "correct" if is_correct else "wrong"
            fb_kwargs = {
                "question": q["question"],
                "user_answer": f"{answer}) {q['options'].get(answer, '')}",
            }
            if not is_correct:
                fb_kwargs["correct_answer"] = f"{q['answer']}) {q['options'][q['answer']]}"
                fb_kwargs["source_text"] = q.get("source_text", "N/A")

            fb_prompt = get_feedback_prompt(style, language, scenario, **fb_kwargs)
            feedback = _get_llm_feedback(system_prompt, fb_prompt)
            if feedback:
                print(f"\n{feedback}")

    # Grade the full quiz
    result = grade_quiz(questions, user_answers)

    # Save score
    save_score(result["score"], result["total"])

    # Show results
    pct_display = result["percentage"] * 100
    print(f"\n{'='*50}")
    if result["passed"]:
        print(f"  PASSED! Score: {result['score']}/{result['total']} ({pct_display:.0f}%)")
    else:
        print(f"  NOT PASSED. Score: {result['score']}/{result['total']} ({pct_display:.0f}%)")
    print(f"{'='*50}")

    # LLM feedback on overall result
    if not config.is_sandbox():
        scenario = "pass" if result["passed"] else "fail"
        fb_prompt = get_feedback_prompt(
            style, language, scenario,
            score=result["score"],
            total=result["total"],
            percentage=f"{pct_display:.0f}",
        )
        feedback = _get_llm_feedback(system_prompt, fb_prompt)
        if feedback:
            print(f"\n{feedback}")

    return result


def _ask_yes_no(prompt: str) -> bool:
    """Ask a yes/no question and return True for yes."""
    while True:
        answer = input(f"\n{prompt} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


def main():
    """Main application entry point."""
    # Step 1: Onboarding — pick style + language
    preferences = run_onboarding()
    style = preferences["style"]
    language = preferences["language"]

    # Generate system prompt
    system_prompt = generate_system_prompt(style, language)

    # Step 2: Initialize RAG (build/load vector store)
    if config.is_sandbox():
        print("[Sandbox Mode] Using mock data — no real API calls.")
    print("\nPreparing study materials...")
    load_vector_store()
    print("Ready!\n")

    # Clear previous wrong answers for a fresh session
    clear_wrong_answers()

    # Step 3: Quiz loop
    while True:
        # Check attempt limit
        if get_attempt_count() >= config.MAX_ATTEMPTS:
            print(f"\nYou've reached the maximum of {config.MAX_ATTEMPTS} attempts.")
            break

        # Run a quiz round
        result = _run_quiz_round(system_prompt, style, language)
        if result is None:
            break

        # Step 4: Review wrong answers?
        if has_wrong_answers():
            if _ask_yes_no(f"You got {get_wrong_count()} question(s) wrong. Review them?"):
                # LLM review intro
                if not config.is_sandbox():
                    fb_prompt = get_feedback_prompt(
                        style, language, "review_intro",
                        wrong_count=get_wrong_count(),
                    )
                    feedback = _get_llm_feedback(system_prompt, fb_prompt)
                    if feedback:
                        print(f"\n{feedback}")

                review_result = run_review_session()
                if review_result["still_wrong"]:
                    print(f"\nStill missed {len(review_result['still_wrong'])} question(s).")
                else:
                    print("\nYou got all review questions right!")

        # Step 5: Try again?
        if not _ask_yes_no("Do you want to take another quiz?"):
            break

        # Clear wrong answers for next round
        clear_wrong_answers()

    # Step 6: Show final score history
    print(get_progress_summary())
    print("Thank you for using Maple Quiz Buddy! Good luck on your citizenship test!\n")


if __name__ == "__main__":
    main()
