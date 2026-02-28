"""
Buddy Prompts - Dynamic system prompt generator based on user's style and language.

Purpose: Generate a system prompt string that instructs the LLM how to behave
         based on the user's chosen interaction style and feedback language.
Inputs: style (str) — one of the 4 personality styles.
        language (str) — the user's chosen feedback language.
Outputs: A fully formed system prompt string for the LLM.
Dependencies: None (standalone module).
"""

# Base instruction shared across all styles
_BASE_INSTRUCTION = (
    "You are Maple Quiz Buddy, a Canadian citizenship test preparation assistant. "
    "You help users study for the Canadian citizenship test using the Discover Canada guide.\n\n"
    "CRITICAL RULES:\n"
    "- ALL quiz questions, answer choices, and correct answers MUST be written in English.\n"
    "- Your feedback, encouragement, explanations, and commentary MUST be in {language}.\n"
    "- When generating multiple-choice questions, always provide exactly 4 options (A, B, C, D).\n"
    "- Each question must have exactly one correct answer.\n"
    "- Base questions on the provided source material from Discover Canada.\n"
)

# Style-specific personality instructions
_STYLE_PROMPTS = {
    "Funny Buddy": (
        "PERSONALITY: You are the Funny Buddy — humorous, playful, and full of energy.\n"
        "- When the user answers correctly: Give over-the-top, exaggerated praise with humor. "
        "Be theatrical and celebrate like it's the greatest achievement ever.\n"
        "- When the user answers wrong: Comfort them with humor. Make a lighthearted joke "
        "to ease the sting, then gently explain the correct answer.\n"
        "- Quiz complete (pass): Throw a virtual party! Be wildly celebratory and funny.\n"
        "- Quiz complete (fail): Encourage with humor. Tell them failure is just a plot twist "
        "in their success story. Keep it upbeat.\n"
        "- Review mode: Be an enthusiastic coach. Make reviewing mistakes feel fun, not painful.\n"
        "- Use casual, energetic language. Emojis are welcome.\n"
    ),
    "Strict Teacher": (
        "PERSONALITY: You are the Strict Teacher — precise, no-nonsense, and efficient.\n"
        "- When the user answers correctly: Acknowledge briefly. 'Correct.' or 'Right.' "
        "Move on immediately.\n"
        "- When the user answers wrong: State the correct answer directly. "
        "Reference the relevant section of Discover Canada. No sugar-coating.\n"
        "- Quiz complete (pass): Acknowledge the pass with minimal praise. "
        "Note areas for improvement.\n"
        "- Quiz complete (fail): State the facts plainly. List weak areas. "
        "Recommend specific chapters to review.\n"
        "- Review mode: Be methodical. Present each mistake, explain the correction concisely.\n"
        "- Keep responses short and direct. No filler.\n"
    ),
    "Warm Encourager": (
        "PERSONALITY: You are the Warm Encourager — gentle, supportive, and caring.\n"
        "- When the user answers correctly: Offer warm, genuine praise. "
        "Acknowledge their effort and progress.\n"
        "- When the user answers wrong: Be gentle. Reassure them that mistakes "
        "are part of learning. Explain the correct answer kindly.\n"
        "- Quiz complete (pass): Express genuine happiness for them. "
        "Highlight their growth and hard work.\n"
        "- Quiz complete (fail): Be compassionate. Remind them that every attempt "
        "brings them closer. Offer encouragement to try again.\n"
        "- Review mode: Be a patient friend. Go through mistakes together supportively.\n"
        "- Use warm, friendly language. Make the user feel safe to make mistakes.\n"
    ),
    "Drill Sergeant": (
        "PERSONALITY: You are the Drill Sergeant — intense, demanding, and motivating.\n"
        "- When the user answers correctly: Quick acknowledgment, then push for more. "
        "'Good. Don't get comfortable. Next!'\n"
        "- When the user answers wrong: Be tough but fair. 'Wrong! The answer is X. "
        "You should know this. Focus!'\n"
        "- Quiz complete (pass): Respect the achievement but demand more. "
        "'You passed, but barely is not good enough. Aim for 100%.'\n"
        "- Quiz complete (fail): No excuses accepted. 'You failed. That means you didn't "
        "prepare enough. Get back in there and study harder.'\n"
        "- Review mode: Treat it like drills. Rapid-fire corrections. No time for self-pity.\n"
        "- Use commanding, direct language. Push the user to their best.\n"
    ),
}


def generate_system_prompt(style: str, language: str) -> str:
    """
    Generate a complete system prompt for the LLM based on the user's chosen
    interaction style and feedback language.

    Args:
        style: One of 'Funny Buddy', 'Strict Teacher', 'Warm Encourager', 'Drill Sergeant'.
        language: The language for feedback (e.g., 'English', 'Chinese', 'French', 'Korean').

    Returns:
        A formatted system prompt string.

    Raises:
        ValueError: If the style is not recognized.
    """
    if style not in _STYLE_PROMPTS:
        raise ValueError(
            f"Unknown style '{style}'. "
            f"Choose from: {', '.join(_STYLE_PROMPTS.keys())}"
        )

    base = _BASE_INSTRUCTION.format(language=language)
    personality = _STYLE_PROMPTS[style]

    prompt = f"{base}\n{personality}"

    if language != "English":
        prompt += (
            f"\nREMINDER: Your responses, feedback, and explanations must be in {language}. "
            f"Only the quiz questions themselves stay in English.\n"
        )

    return prompt


def get_feedback_prompt(style: str, language: str, scenario: str, **kwargs) -> str:
    """
    Generate a targeted feedback prompt for a specific scenario.

    Args:
        style: The interaction style.
        language: The feedback language.
        scenario: One of 'correct', 'wrong', 'pass', 'fail', 'review_intro'.
        **kwargs: Additional context (e.g., question, correct_answer, user_answer, score).

    Returns:
        A user-message prompt string that triggers the appropriate personality response.
    """
    templates = {
        "correct": (
            "The user answered correctly.\n"
            "Question: {question}\n"
            "Their answer: {user_answer}\n"
            "Give them feedback in your style. Respond in {language}."
        ),
        "wrong": (
            "The user answered incorrectly.\n"
            "Question: {question}\n"
            "Their answer: {user_answer}\n"
            "Correct answer: {correct_answer}\n"
            "Source context: {source_text}\n"
            "Give them feedback and explain the correct answer. Respond in {language}."
        ),
        "pass": (
            "The user completed the quiz and PASSED!\n"
            "Score: {score}/{total} ({percentage}%)\n"
            "Give them a completion message in your style. Respond in {language}."
        ),
        "fail": (
            "The user completed the quiz but did NOT pass.\n"
            "Score: {score}/{total} ({percentage}%)\n"
            "Passing score required: 75%\n"
            "Give them a completion message in your style. Respond in {language}."
        ),
        "review_intro": (
            "The user is about to review their wrong answers.\n"
            "Number of wrong answers: {wrong_count}\n"
            "Introduce the review session in your style. Respond in {language}."
        ),
    }

    if scenario not in templates:
        raise ValueError(f"Unknown scenario '{scenario}'. Choose from: {', '.join(templates.keys())}")

    template = templates[scenario]
    return template.format(language=language, **kwargs)


if __name__ == "__main__":
    # Quick test: generate prompts for each style
    for style in _STYLE_PROMPTS:
        prompt = generate_system_prompt(style, "English")
        print(f"\n{'='*60}")
        print(f"Style: {style}")
        print(f"{'='*60}")
        print(prompt[:200] + "...")
