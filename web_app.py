"""
Maple Quiz Buddy — Streamlit Web Frontend

Purpose: Browser-based UI for the Canadian citizenship quiz app.
Run with: streamlit run web_app.py
Dependencies: All project modules + streamlit.
"""

import streamlit as st
import config
from personality.style_selector import STYLES, LANGUAGES, STYLE_DESCRIPTIONS
from personality.buddy_prompts import generate_system_prompt, get_feedback_prompt
from rag.vector_store import load_vector_store
from quiz.question_generator import generate_questions
from quiz.grader import grade_quiz, grade_answer, clear_wrong_answers
from quiz.review_manager import get_review_questions, has_wrong_answers, get_wrong_count
from memory.score_tracker import (
    save_score, load_score_history, get_attempt_count, clear_score_history,
)

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Maple Quiz Buddy",
    page_icon="🍁",
    layout="centered",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    /* Header bar */
    .stApp > header {
        background-color: #FF0000;
    }
    /* Title styling */
    .maple-title {
        color: #FF0000;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0;
    }
    .maple-subtitle {
        color: #666;
        text-align: center;
        font-size: 1.1rem;
        margin-top: 0;
    }
    /* Red divider */
    .red-divider {
        border: none;
        border-top: 3px solid #FF0000;
        margin: 1rem 0;
    }
    /* Score card */
    .score-card {
        background: linear-gradient(135deg, #FF0000 0%, #CC0000 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    .score-card h1 {
        font-size: 3rem;
        margin: 0;
        color: white;
    }
    .score-card p {
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        color: #FFD4D4;
    }
    /* Pass/Fail banners */
    .pass-banner {
        background: #28a745;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .fail-banner {
        background: #dc3545;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    /* Question card */
    .question-card {
        background: #FFF5F5;
        border-left: 4px solid #FF0000;
        padding: 1.5rem;
        border-radius: 0 0.5rem 0.5rem 0;
        margin: 1rem 0;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #FFF8F8;
    }
    /* Button styling */
    .stButton > button {
        background-color: #FF0000;
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #CC0000;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ── Cached Resources ─────────────────────────────────────────
@st.cache_resource(show_spinner="Loading study materials...")
def init_vector_store():
    """Load vector store once and cache it."""
    return load_vector_store()


# ── LLM Feedback Helper ─────────────────────────────────────
def get_llm_feedback(system_prompt: str, feedback_prompt: str) -> str:
    """Get personality-based feedback from the LLM."""
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
        return f"(Feedback unavailable: {e})"


# ── Session State Initialization ─────────────────────────────
def init_state():
    """Initialize session state with defaults."""
    defaults = {
        "phase": "onboarding",
        "style": None,
        "language": None,
        "system_prompt": "",
        "questions": [],
        "current_q": 0,
        "user_answers": [],
        "answered": False,
        "feedback_text": "",
        "quiz_result": None,
        # Review mode
        "review_questions": [],
        "review_current_q": 0,
        "review_answers": [],
        "review_answered": False,
        "review_feedback": "",
        "review_result": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_state()


# ── Header ───────────────────────────────────────────────────
def render_header():
    """Render the app header with maple leaf."""
    st.markdown(
        '<div style="text-align:center;">'
        '<span style="font-size:4rem;">🍁</span><br>'
        '<p class="maple-title">Maple Quiz Buddy</p>'
        '<p class="maple-subtitle">Canadian Citizenship Test Prep</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="red-divider">', unsafe_allow_html=True)


# ── Phase: Onboarding ───────────────────────────────────────
def render_onboarding():
    """Render the onboarding page with style and language selection."""
    st.markdown("### Welcome! Let's set up your quiz experience.")

    if config.is_sandbox():
        st.info("🔧 Sandbox Mode — Using mock data (no API calls)")

    st.markdown("#### Choose Your Quiz Buddy Style")

    style_names = list(STYLES.values())
    style_choice = st.radio(
        "Pick a personality:",
        style_names,
        format_func=lambda s: f"{s} — {STYLE_DESCRIPTIONS[s]}",
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("#### Choose Feedback Language")
    st.caption("Quiz questions are always in English. Feedback uses your chosen language.")

    lang_options = list(LANGUAGES.values()) + ["Other"]
    lang_choice = st.selectbox("Language:", lang_options, index=0)

    custom_lang = ""
    if lang_choice == "Other":
        custom_lang = st.text_input("Type your language:")

    st.markdown("---")

    if st.button("🍁 Start Quiz", use_container_width=True):
        final_lang = custom_lang if lang_choice == "Other" and custom_lang else lang_choice
        if lang_choice == "Other" and not custom_lang:
            st.warning("Please type a language.")
            return

        st.session_state.style = style_choice
        st.session_state.language = final_lang
        st.session_state.system_prompt = generate_system_prompt(style_choice, final_lang)

        # Initialize vector store
        init_vector_store()

        # Clear previous data
        clear_wrong_answers()

        # Generate questions
        with st.spinner("Generating quiz questions..."):
            st.session_state.questions = generate_questions(
                num_questions=config.QUESTIONS_PER_QUIZ,
                system_prompt=st.session_state.system_prompt,
            )
        st.session_state.user_answers = []
        st.session_state.current_q = 0
        st.session_state.answered = False
        st.session_state.feedback_text = ""
        st.session_state.phase = "quiz"
        st.rerun()


# ── Phase: Quiz ──────────────────────────────────────────────
def render_quiz():
    """Render the quiz page — one question at a time."""
    questions = st.session_state.questions
    idx = st.session_state.current_q
    total = len(questions)

    if idx >= total:
        # All questions answered — grade and move to results
        _finish_quiz()
        return

    q = questions[idx]

    # Progress
    st.progress((idx) / total, text=f"Question {idx + 1} of {total}")

    # Attempt info
    attempt = get_attempt_count() + 1
    st.caption(f"Attempt #{attempt} · Style: {st.session_state.style} · Language: {st.session_state.language}")

    # Question card
    st.markdown(f'<div class="question-card"><strong>Q{idx + 1}.</strong> {q["question"]}</div>', unsafe_allow_html=True)

    # Options
    option_labels = [f"{letter}) {text}" for letter, text in q["options"].items()]
    selected = st.radio(
        "Choose your answer:",
        option_labels,
        index=None,
        key=f"q_{idx}",
        label_visibility="collapsed",
    )

    if not st.session_state.answered:
        if st.button("Submit Answer", use_container_width=True, disabled=selected is None):
            if selected is None:
                st.warning("Please select an answer.")
                return

            answer_letter = selected[0]  # "A) ..." → "A"
            st.session_state.user_answers.append(answer_letter)
            st.session_state.answered = True

            # Get feedback
            is_correct = grade_answer(q, answer_letter)
            if config.is_sandbox():
                if is_correct:
                    st.session_state.feedback_text = "✅ Correct!"
                else:
                    correct = q["answer"]
                    st.session_state.feedback_text = f"❌ Wrong. The correct answer is: {correct}) {q['options'][correct]}"
            else:
                scenario = "correct" if is_correct else "wrong"
                fb_kwargs = {
                    "question": q["question"],
                    "user_answer": f"{answer_letter}) {q['options'].get(answer_letter, '')}",
                }
                if not is_correct:
                    fb_kwargs["correct_answer"] = f"{q['answer']}) {q['options'][q['answer']]}"
                    fb_kwargs["source_text"] = q.get("source_text", "N/A")

                fb_prompt = get_feedback_prompt(
                    st.session_state.style,
                    st.session_state.language,
                    scenario, **fb_kwargs,
                )
                with st.spinner("Getting feedback..."):
                    st.session_state.feedback_text = get_llm_feedback(
                        st.session_state.system_prompt, fb_prompt
                    )
                    if not st.session_state.feedback_text:
                        if is_correct:
                            st.session_state.feedback_text = "✅ Correct!"
                        else:
                            correct = q["answer"]
                            st.session_state.feedback_text = f"❌ Wrong. The correct answer is: {correct}) {q['options'][correct]}"

            st.rerun()
    else:
        # Show feedback
        feedback = st.session_state.feedback_text
        answer_letter = st.session_state.user_answers[-1]
        is_correct = grade_answer(q, answer_letter)

        if is_correct:
            st.success(feedback)
        else:
            st.error(feedback)

        if st.button("Next Question →", use_container_width=True):
            st.session_state.current_q += 1
            st.session_state.answered = False
            st.session_state.feedback_text = ""
            st.rerun()


def _finish_quiz():
    """Grade the quiz and transition to results phase."""
    result = grade_quiz(st.session_state.questions, st.session_state.user_answers)
    save_score(result["score"], result["total"])
    st.session_state.quiz_result = result

    # Get LLM completion feedback
    if not config.is_sandbox():
        pct = result["percentage"] * 100
        scenario = "pass" if result["passed"] else "fail"
        fb_prompt = get_feedback_prompt(
            st.session_state.style,
            st.session_state.language,
            scenario,
            score=result["score"],
            total=result["total"],
            percentage=f"{pct:.0f}",
        )
        result["completion_feedback"] = get_llm_feedback(
            st.session_state.system_prompt, fb_prompt
        )
    else:
        result["completion_feedback"] = ""

    st.session_state.phase = "results"
    st.rerun()


# ── Phase: Results ───────────────────────────────────────────
def render_results():
    """Render the quiz results page."""
    result = st.session_state.quiz_result
    if not result:
        st.session_state.phase = "onboarding"
        st.rerun()
        return

    score = result["score"]
    total = result["total"]
    pct = result["percentage"] * 100

    # Score card
    st.markdown(
        f'<div class="score-card">'
        f'<h1>{score}/{total}</h1>'
        f'<p>{pct:.0f}%</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Pass/Fail banner
    if result["passed"]:
        st.markdown('<div class="pass-banner">🎉 PASSED!</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="fail-banner">❌ NOT PASSED (need 75%)</div>', unsafe_allow_html=True)

    # LLM feedback
    if result.get("completion_feedback"):
        st.markdown("---")
        st.markdown(result["completion_feedback"])

    st.markdown("---")

    # Action buttons
    wrong_count = get_wrong_count()
    col1, col2, col3 = st.columns(3)

    with col1:
        if wrong_count > 0:
            if st.button(f"📝 Review ({wrong_count} wrong)", use_container_width=True):
                _start_review()

    with col2:
        if get_attempt_count() < config.MAX_ATTEMPTS:
            if st.button("🔄 Try Again", use_container_width=True):
                _start_new_quiz()
        else:
            st.caption(f"Max attempts ({config.MAX_ATTEMPTS}) reached")

    with col3:
        if st.button("📊 Score History", use_container_width=True):
            st.session_state.phase = "history"
            st.rerun()


def _start_review():
    """Initialize review mode."""
    st.session_state.review_questions = get_review_questions()
    st.session_state.review_current_q = 0
    st.session_state.review_answers = []
    st.session_state.review_answered = False
    st.session_state.review_feedback = ""
    st.session_state.review_result = None
    st.session_state.phase = "review"
    st.rerun()


def _start_new_quiz():
    """Start a new quiz attempt."""
    clear_wrong_answers()
    with st.spinner("Generating new questions..."):
        st.session_state.questions = generate_questions(
            num_questions=config.QUESTIONS_PER_QUIZ,
            system_prompt=st.session_state.system_prompt,
        )
    st.session_state.user_answers = []
    st.session_state.current_q = 0
    st.session_state.answered = False
    st.session_state.feedback_text = ""
    st.session_state.quiz_result = None
    st.session_state.phase = "quiz"
    st.rerun()


# ── Phase: Review ────────────────────────────────────────────
def render_review():
    """Render the review mode — re-quiz on wrong answers."""
    questions = st.session_state.review_questions
    idx = st.session_state.review_current_q
    total = len(questions)

    if not questions:
        st.info("No wrong answers to review.")
        if st.button("← Back to Results"):
            st.session_state.phase = "results"
            st.rerun()
        return

    if idx >= total:
        _finish_review()
        return

    st.markdown("### 📝 Review Mode")
    st.progress(idx / total, text=f"Review {idx + 1} of {total}")

    q = questions[idx]

    st.markdown(f'<div class="question-card"><strong>Q{idx + 1}.</strong> {q["question"]}</div>', unsafe_allow_html=True)

    option_labels = [f"{letter}) {text}" for letter, text in q["options"].items()]
    selected = st.radio(
        "Choose your answer:",
        option_labels,
        index=None,
        key=f"review_{idx}",
        label_visibility="collapsed",
    )

    if not st.session_state.review_answered:
        if st.button("Submit Answer", use_container_width=True, disabled=selected is None):
            if selected is None:
                st.warning("Please select an answer.")
                return

            answer_letter = selected[0]
            st.session_state.review_answers.append(answer_letter)
            st.session_state.review_answered = True

            is_correct = grade_answer(q, answer_letter)
            if is_correct:
                st.session_state.review_feedback = "✅ Correct!"
            else:
                correct = q["answer"]
                st.session_state.review_feedback = (
                    f"❌ Wrong. The correct answer is: {correct}) {q['options'][correct]}"
                )
                if q.get("source_text"):
                    st.session_state.review_feedback += f"\n\n📖 Source: {q['source_text']}"

            st.rerun()
    else:
        feedback = st.session_state.review_feedback
        answer_letter = st.session_state.review_answers[-1]
        is_correct = grade_answer(q, answer_letter)

        if is_correct:
            st.success(feedback)
        else:
            st.error(feedback)

        if st.button("Next →", use_container_width=True):
            st.session_state.review_current_q += 1
            st.session_state.review_answered = False
            st.session_state.review_feedback = ""
            st.rerun()


def _finish_review():
    """Calculate review results and display."""
    questions = st.session_state.review_questions
    answers = st.session_state.review_answers

    correct = sum(
        1 for q, a in zip(questions, answers) if grade_answer(q, a)
    )
    total = len(questions)
    pct = correct / total if total > 0 else 0

    st.markdown("### 📝 Review Complete!")

    st.markdown(
        f'<div class="score-card">'
        f'<h1>{correct}/{total}</h1>'
        f'<p>Review Score: {pct*100:.0f}%</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if correct == total:
        st.success("You got all review questions right! Great job!")
    else:
        still_wrong = total - correct
        st.warning(f"Still missed {still_wrong} question(s). Keep studying!")

    col1, col2 = st.columns(2)
    with col1:
        if get_attempt_count() < config.MAX_ATTEMPTS:
            if st.button("🔄 New Quiz", use_container_width=True):
                _start_new_quiz()
    with col2:
        if st.button("📊 Score History", use_container_width=True):
            st.session_state.phase = "history"
            st.rerun()


# ── Phase: Score History ─────────────────────────────────────
def render_history():
    """Render score history page."""
    st.markdown("### 📊 Score History")

    history = load_score_history()

    if not history:
        st.info("No quiz attempts recorded yet.")
    else:
        # Table
        import pandas as pd
        df = pd.DataFrame(history)
        df["status"] = df["percentage"].apply(
            lambda p: "✅ PASS" if p >= config.PASSING_SCORE else "❌ FAIL"
        )
        df["percentage"] = df["percentage"].apply(lambda p: f"{p*100:.0f}%")
        df.columns = ["Attempt", "Date", "Score", "Total", "Percentage", "Status"]

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Stats
        scores = [e["percentage"] for e in history]
        # Recalculate from raw data (percentage stored as float)
        raw_pcts = [e["score"] / e["total"] for e in history]
        best = max(raw_pcts) * 100
        worst = min(raw_pcts) * 100
        avg = sum(raw_pcts) / len(raw_pcts) * 100
        passes = sum(1 for p in raw_pcts if p >= config.PASSING_SCORE)

        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Attempts", len(history))
        col2.metric("Passed", f"{passes}/{len(history)}")
        col3.metric("Best Score", f"{best:.0f}%")
        col4.metric("Average", f"{avg:.0f}%")

        # Trend
        if len(raw_pcts) >= 2:
            if raw_pcts[-1] > raw_pcts[-2]:
                st.success("📈 Trend: Improving! Keep it up!")
            elif raw_pcts[-1] < raw_pcts[-2]:
                st.warning("📉 Trend: Score dropped. Review your weak areas.")
            else:
                st.info("➡️ Trend: Steady. Push for improvement!")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if get_attempt_count() < config.MAX_ATTEMPTS:
            if st.button("🔄 New Quiz", use_container_width=True):
                _start_new_quiz()
    with col2:
        if st.button("🏠 Back to Start", use_container_width=True):
            # Reset everything
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ── Main Router ──────────────────────────────────────────────
def main():
    render_header()

    phase = st.session_state.phase

    if phase == "onboarding":
        render_onboarding()
    elif phase == "quiz":
        render_quiz()
    elif phase == "results":
        render_results()
    elif phase == "review":
        render_review()
    elif phase == "history":
        render_history()


if __name__ == "__main__":
    main()
