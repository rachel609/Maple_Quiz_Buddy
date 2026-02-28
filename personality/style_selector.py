"""
Style Selector - Onboarding module for user interaction preferences.

Purpose: Collect the user's preferred interaction style and language at app startup.
Inputs: User input via CLI prompts.
Outputs: A dict with keys 'style' (str) and 'language' (str).
Dependencies: None (standalone module).
"""

# Available interaction styles
STYLES = {
    "1": "Funny Buddy",
    "2": "Strict Teacher",
    "3": "Warm Encourager",
    "4": "Drill Sergeant",
}

# Preset language options
LANGUAGES = {
    "1": "English",
    "2": "Chinese",
    "3": "French",
    "4": "Korean",
}

STYLE_DESCRIPTIONS = {
    "Funny Buddy": "Humorous and playful. Over-the-top praise when correct, funny comfort when wrong.",
    "Strict Teacher": "Precise and no-nonsense. Short feedback, straight to the point.",
    "Warm Encourager": "Gentle and supportive. Like a friend cheering you on.",
    "Drill Sergeant": "High-pressure motivator. Pushes you to do better, no excuses.",
}


def select_style() -> str:
    """Prompt the user to pick an interaction style. Returns the style name string."""
    print("\n========================================")
    print("   Welcome to Maple Quiz Buddy!")
    print("   Canadian Citizenship Test Prep")
    print("========================================\n")
    print("First, pick your quiz buddy style:\n")

    for key, name in STYLES.items():
        print(f"  {key}. {name} — {STYLE_DESCRIPTIONS[name]}")

    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        if choice in STYLES:
            selected = STYLES[choice]
            print(f"\n-> You picked: {selected}")
            return selected
        print("Invalid choice. Please enter a number between 1 and 4.")


def select_language() -> str:
    """Prompt the user to pick a feedback language. Returns the language name string."""
    print("\nNow, choose the language for feedback and encouragement:")
    print("(Quiz questions are always in English)\n")

    for key, name in LANGUAGES.items():
        print(f"  {key}. {name}")
    print("  5. Other (type your own)")

    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in LANGUAGES:
            selected = LANGUAGES[choice]
            print(f"\n-> Feedback language: {selected}")
            return selected
        if choice == "5":
            custom = input("Type your preferred language: ").strip()
            if custom:
                print(f"\n-> Feedback language: {custom}")
                return custom
            print("Language cannot be empty. Try again.")
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


def run_onboarding() -> dict:
    """Run the full onboarding flow. Returns {'style': str, 'language': str}."""
    style = select_style()
    language = select_language()
    print(f"\nGreat! Starting quiz with {style} style in {language}.\n")
    return {"style": style, "language": language}


if __name__ == "__main__":
    result = run_onboarding()
    print(f"Onboarding result: {result}")
