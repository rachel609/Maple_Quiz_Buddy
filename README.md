# 🍁 Maple Quiz Buddy

**An AI-powered Canadian Citizenship Test prep tool built with LangChain, Grok LLM, and RAG.**

Maple Quiz Buddy uses Retrieval-Augmented Generation (RAG) to intelligently generate quiz questions from the official *Discover Canada* study guide, then delivers personalized feedback through four distinct AI personalities — all wrapped in a clean Streamlit web interface with a Canadian red-and-white theme.

---

## Features

### Intelligent Question Generation (RAG + LLM)
- Chunks the official *Discover Canada* PDF and embeds it into a **ChromaDB** vector store
- Retrieves relevant passages per topic, then uses **xAI Grok** to generate diverse, context-aware multiple-choice questions
- Every quiz is unique — questions and answer options are dynamically shuffled

### Four AI Personality Modes
| Style | Vibe |
|-------|------|
| 🎭 **Funny Buddy** | Over-the-top praise, humorous comfort when wrong |
| 📏 **Strict Teacher** | No-nonsense, straight to the point |
| 💛 **Warm Encourager** | Gentle, supportive, like a friend cheering you on |
| 🎖️ **Drill Sergeant** | High-pressure motivator, no excuses |

### Multilingual Feedback
- Quiz questions are always in **English** (matching the real test)
- AI feedback and encouragement in your chosen language: English, Chinese, French, Korean, or any custom language

### Full Quiz Flow
```
Choose Personality + Language
        ↓
  RAG: PDF → ChromaDB
        ↓
  20 AI-Generated Questions
        ↓
  Answer One-by-One with Instant AI Feedback
        ↓
  Score + Pass/Fail (75% threshold)
        ↓
  Review Wrong Answers (shuffled re-quiz)
        ↓
  Multi-Attempt Score History + Trend Analysis
```

### Streamlit Web UI
- 🍁 Canadian red-and-white themed interface
- Progress bar, score cards, and interactive radio buttons
- Score history dashboard with pass/fail tracking and trend analysis
- Also available as a CLI app (`python app.py`)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | [xAI Grok](https://x.ai/) via `langchain-xai` |
| **RAG Framework** | [LangChain](https://www.langchain.com/) |
| **Vector Store** | [ChromaDB](https://www.trychroma.com/) with ONNX Runtime embeddings |
| **PDF Processing** | PyPDF + LangChain RecursiveCharacterTextSplitter |
| **Frontend** | [Streamlit](https://streamlit.io/) |
| **Language** | Python 3.10+ |

---

## Architecture

```
app.py / web_app.py          ← Entry points (CLI / Web)
 │
 ├─ personality/
 │   ├─ style_selector.py    ← Onboarding: pick style + language
 │   └─ buddy_prompts.py     ← Dynamic system prompt generation
 │
 ├─ rag/
 │   ├─ pdf_loader.py        ← PDF → chunked Documents
 │   └─ vector_store.py      ← ChromaDB embed + retrieve
 │
 ├─ quiz/
 │   ├─ question_generator.py ← RAG retrieval + Grok question generation
 │   ├─ grader.py             ← Answer grading + wrong answer logging
 │   └─ review_manager.py     ← Wrong answer review + shuffled re-quiz
 │
 └─ memory/
     └─ score_tracker.py      ← Multi-attempt score tracking + progress
```

---

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/rachel609/Maple_Quiz_Buddy.git
cd Maple_Quiz_Buddy
pip install -r requirements.txt
```

### 2. Set Up API Key

```bash
cp .env.example .env
# Edit .env and add your xAI API key
```

Get your xAI API key at [console.x.ai](https://console.x.ai/)

### 3. Download Study Material

Download the official [Discover Canada PDF](https://www.canada.ca/content/dam/ircc/migration/ircc/english/pdf/pub/discover.pdf) and place it in the `data/` directory:

```bash
curl -o data/discover_canada.pdf https://www.canada.ca/content/dam/ircc/migration/ircc/english/pdf/pub/discover.pdf
```

### 4. Run

**Web UI (recommended):**
```bash
streamlit run web_app.py
```

**CLI:**
```bash
python app.py
```

---

## Sandbox Mode

No API key? No problem. The app runs in **sandbox mode** automatically when using the default test key — all modules return mock data so you can explore the full flow without any external API calls.

---

## Project Structure

```
Maple_Quiz_Buddy/
├── .env.example              # Template for API keys
├── .gitignore
├── config.py                 # Global configuration
├── requirements.txt          # Dependencies
├── app.py                    # CLI entry point
├── web_app.py                # Streamlit web entry point
├── assets/
│   └── maple_leaf.svg        # Logo asset
├── personality/
│   ├── style_selector.py     # Onboarding flow
│   └── buddy_prompts.py      # LLM personality prompts
├── rag/
│   ├── pdf_loader.py         # PDF loading + chunking
│   └── vector_store.py       # ChromaDB vector store
├── quiz/
│   ├── question_generator.py # RAG + LLM question generation
│   ├── grader.py             # Grading + wrong answer logging
│   └── review_manager.py     # Wrong answer review
├── memory/
│   └── score_tracker.py      # Score history + progress analysis
└── data/
    └── discover_canada.pdf   # Study material (user downloads)
```

---

## Key Design Decisions

- **ChromaDB Default Embeddings**: Uses ChromaDB's built-in ONNX Runtime embeddings (`all-MiniLM-L6-v2`) — no need to install `sentence-transformers` or heavy ML frameworks
- **LangChain Compatibility Layer**: Custom `_ChromaDefaultEmbeddings` wrapper bridges ChromaDB's native embedding function with LangChain's interface
- **Graceful Degradation**: If the LLM API fails, the app falls back to pre-built mock questions automatically
- **Option Shuffling**: Post-generation shuffle of answer positions prevents LLM bias toward placing correct answers in position A

---

## License

MIT

---

*Built with ❤️ and 🍁 — because every new Canadian deserves a study buddy.*
