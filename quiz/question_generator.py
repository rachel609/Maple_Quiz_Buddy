"""
Question Generator - Generate multiple-choice quiz questions via RAG + Grok LLM.

Purpose: Retrieve relevant passages from the vector store, then use Grok to
         generate multiple-choice questions based on those passages.
Inputs: Number of questions to generate, system prompt from buddy_prompts.
Outputs: A list of question dicts, each with 'question', 'options', 'answer', 'source_text'.
Dependencies: config.py, rag/vector_store.py, personality/buddy_prompts.py, langchain-xai.
"""

import json
import random
import config
from rag.vector_store import retrieve

# Topics to query for diverse question coverage
_QUERY_TOPICS = [
    "Canadian history and Confederation",
    "Rights and responsibilities of citizens",
    "Canadian government structure",
    "Provinces and territories of Canada",
    "Canadian symbols and national anthem",
    "Aboriginal peoples in Canada",
    "Canadian elections and voting",
    "Canadian geography and regions",
    "Famous Canadians and heroes",
    "Canadian military history and wars",
    "Canadian economy and trade",
    "Official languages of Canada",
    "Canadian justice system and law",
    "Canadian cultural heritage",
    "Immigration and citizenship process",
]

# Mock questions for sandbox mode
_MOCK_QUESTIONS = [
    {
        "question": "What is the capital of Canada?",
        "options": {"A": "Toronto", "B": "Ottawa", "C": "Vancouver", "D": "Montreal"},
        "answer": "B",
        "source_text": "The capital of Canada is Ottawa. Ottawa is located in the province of Ontario.",
    },
    {
        "question": "How many provinces does Canada have?",
        "options": {"A": "8", "B": "12", "C": "10", "D": "13"},
        "answer": "C",
        "source_text": "Canada has ten provinces and three territories.",
    },
    {
        "question": "When did Canada become a country?",
        "options": {"A": "July 1, 1867", "B": "July 4, 1776", "C": "January 1, 1901", "D": "March 15, 1842"},
        "answer": "A",
        "source_text": "Canada became a country on July 1, 1867, through the British North America Act.",
    },
    {
        "question": "Who was the first Prime Minister of Canada?",
        "options": {"A": "Wilfrid Laurier", "B": "John A. Macdonald", "C": "Pierre Trudeau", "D": "Alexander Mackenzie"},
        "answer": "B",
        "source_text": "Sir John A. Macdonald was the first Prime Minister of Canada.",
    },
    {
        "question": "What document guarantees fundamental freedoms in Canada?",
        "options": {"A": "The Bill of Rights", "B": "The Magna Carta", "C": "The Charter of Rights and Freedoms", "D": "The Constitution Act"},
        "answer": "C",
        "source_text": "The Canadian Charter of Rights and Freedoms guarantees fundamental freedoms.",
    },
    {
        "question": "What are the three branches of government in Canada?",
        "options": {"A": "Federal, Provincial, Municipal", "B": "Executive, Legislative, Judicial", "C": "Senate, House, Court", "D": "Monarch, Parliament, Military"},
        "answer": "B",
        "source_text": "The three branches of government in Canada are: the Executive, the Legislative, and the Judicial.",
    },
    {
        "question": "What are Canada's official languages?",
        "options": {"A": "English only", "B": "English and Spanish", "C": "English and French", "D": "English, French, and Chinese"},
        "answer": "C",
        "source_text": "Canada's official languages are English and French.",
    },
    {
        "question": "When was the Canadian flag officially adopted?",
        "options": {"A": "1867", "B": "1945", "C": "1965", "D": "1982"},
        "answer": "C",
        "source_text": "The Canadian flag was officially adopted on February 15, 1965.",
    },
    {
        "question": "What is the name of Canada's national police force?",
        "options": {"A": "FBI", "B": "RCMP", "C": "CSIS", "D": "OPP"},
        "answer": "B",
        "source_text": "The Royal Canadian Mounted Police (RCMP) is Canada's national police force.",
    },
    {
        "question": "Which war helped establish a sense of Canadian identity?",
        "options": {"A": "World War I", "B": "The Seven Years' War", "C": "The War of 1812", "D": "The Boer War"},
        "answer": "C",
        "source_text": "The War of 1812 was a defining moment in Canadian history and helped establish a sense of Canadian identity.",
    },
    {
        "question": "What is Remembrance Day in Canada?",
        "options": {"A": "A day to celebrate independence", "B": "A day to honor armed forces members", "C": "A day to celebrate multiculturalism", "D": "A national holiday for shopping"},
        "answer": "B",
        "source_text": "Remembrance Day honors the members of the armed forces who have served and sacrificed.",
    },
    {
        "question": "Who represents the Sovereign in Canada?",
        "options": {"A": "The Prime Minister", "B": "The Chief Justice", "C": "The Governor General", "D": "The Speaker of the House"},
        "answer": "C",
        "source_text": "The Governor General represents the Sovereign (King or Queen) in Canada.",
    },
    {
        "question": "What is the upper house of Parliament called?",
        "options": {"A": "House of Commons", "B": "The Senate", "C": "The Assembly", "D": "The Cabinet"},
        "answer": "B",
        "source_text": "The Senate is the upper house of the Parliament of Canada.",
    },
    {
        "question": "Which province is the only officially bilingual province?",
        "options": {"A": "Quebec", "B": "Ontario", "C": "New Brunswick", "D": "Manitoba"},
        "answer": "C",
        "source_text": "New Brunswick is the only officially bilingual province.",
    },
    {
        "question": "Who ran the Marathon of Hope?",
        "options": {"A": "Wayne Gretzky", "B": "Terry Fox", "C": "Rick Hansen", "D": "Tommy Douglas"},
        "answer": "B",
        "source_text": "Terry Fox ran across Canada in 1980 in his Marathon of Hope to raise money for cancer research.",
    },
    {
        "question": "Which Aboriginal groups are recognized in the Canadian Constitution?",
        "options": {"A": "First Nations only", "B": "Inuit and Metis only", "C": "First Nations, Inuit, and Metis", "D": "All indigenous groups worldwide"},
        "answer": "C",
        "source_text": "Aboriginal peoples in Canada include First Nations, Inuit, and Metis.",
    },
    {
        "question": "What electoral system does Canada use?",
        "options": {"A": "Proportional representation", "B": "Ranked-choice voting", "C": "First-past-the-post", "D": "Two-round system"},
        "answer": "C",
        "source_text": "Canada uses a first-past-the-post electoral system.",
    },
    {
        "question": "What is one responsibility of Canadian citizenship?",
        "options": {"A": "Paying tithes", "B": "Serving on a jury", "C": "Joining the military", "D": "Learning both official languages"},
        "answer": "B",
        "source_text": "The responsibilities of Canadian citizenship include serving on a jury.",
    },
    {
        "question": "What year was the Constitution patriated from Britain?",
        "options": {"A": "1867", "B": "1931", "C": "1982", "D": "1999"},
        "answer": "C",
        "source_text": "The Constitution Act of 1982 patriated the Constitution from Britain.",
    },
    {
        "question": "Canada is a member of which international economic group?",
        "options": {"A": "G20 only", "B": "BRICS", "C": "G7", "D": "ASEAN"},
        "answer": "C",
        "source_text": "Canada is a major trading nation and a member of the G7.",
    },
]

# Prompt template for generating questions via LLM
_GENERATION_PROMPT = """Based on the following source material from the Discover Canada guide, generate {count} multiple-choice quiz questions for Canadian citizenship test preparation.

SOURCE MATERIAL:
{context}

RULES:
- Each question must have exactly 4 options (A, B, C, D)
- Exactly one option must be the correct answer
- Questions must be in English
- Questions should test factual knowledge from the source material
- Vary the difficulty: include easy, medium, and hard questions

Return your response as a valid JSON array. Each element must have these exact keys:
- "question": the question text (string)
- "options": an object with keys "A", "B", "C", "D" and their answer text values
- "answer": the letter of the correct answer ("A", "B", "C", or "D")
- "source_text": a brief quote or paraphrase from the source that supports the correct answer

Return ONLY the JSON array, no other text.
"""


def generate_questions(num_questions: int = None, system_prompt: str = "") -> list:
    """
    Generate multiple-choice quiz questions using RAG + LLM.

    In sandbox mode, returns mock questions without calling the API.

    Args:
        num_questions: Number of questions to generate. Defaults to config.QUESTIONS_PER_QUIZ.
        system_prompt: The system prompt from buddy_prompts (sets personality).

    Returns:
        A list of question dicts with keys: question, options, answer, source_text.
    """
    if num_questions is None:
        num_questions = config.QUESTIONS_PER_QUIZ

    if config.is_sandbox():
        return _generate_mock_questions(num_questions)

    return _generate_llm_questions(num_questions, system_prompt)


def _generate_mock_questions(num_questions: int) -> list:
    """Return shuffled mock questions for sandbox testing."""
    print(f"[Sandbox] Generating {num_questions} mock questions...")
    questions = _MOCK_QUESTIONS.copy()
    random.shuffle(questions)
    return questions[:num_questions]


def _generate_llm_questions(num_questions: int, system_prompt: str) -> list:
    """Generate questions using RAG retrieval + Grok LLM."""
    from langchain_xai import ChatXAI
    from langchain_core.prompts import ChatPromptTemplate

    # Retrieve diverse context from vector store
    all_context = []
    topics = random.sample(_QUERY_TOPICS, min(len(_QUERY_TOPICS), 8))
    for topic in topics:
        docs = retrieve(topic, k=2)
        for doc in docs:
            if doc.page_content not in all_context:
                all_context.append(doc.page_content)

    context_text = "\n\n---\n\n".join(all_context)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt if system_prompt else "You are a quiz question generator."),
        ("human", _GENERATION_PROMPT),
    ])

    try:
        llm = ChatXAI(model=config.GROK_MODEL, api_key=config.XAI_API_KEY)
        chain = prompt | llm
        response = chain.invoke({
            "count": num_questions,
            "context": context_text,
        })

        questions = _parse_questions_response(response.content)

        if len(questions) < num_questions:
            print(f"Warning: LLM returned {len(questions)} questions, requested {num_questions}.")

        return questions[:num_questions]

    except Exception as e:
        print(f"Error generating questions via LLM: {e}")
        print("Falling back to mock questions...")
        return _generate_mock_questions(num_questions)


def _parse_questions_response(response_text: str) -> list:
    """Parse the LLM response JSON into a list of question dicts."""
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        questions = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response as JSON: {e}")
        return []

    if not isinstance(questions, list):
        return []

    valid = []
    for q in questions:
        if all(k in q for k in ("question", "options", "answer", "source_text")):
            if isinstance(q["options"], dict) and q["answer"] in ("A", "B", "C", "D"):
                valid.append(q)
    return [_shuffle_options(q) for q in valid]


def _shuffle_options(question: dict) -> dict:
    """
    Shuffle the option order (A/B/C/D) randomly so the correct answer
    isn't always in the same position. Updates the answer key accordingly.
    """
    options = question["options"]
    correct_text = options[question["answer"]]

    # Collect option texts and shuffle
    texts = list(options.values())
    random.shuffle(texts)

    # Reassign to A/B/C/D
    letters = ["A", "B", "C", "D"]
    new_options = dict(zip(letters, texts))
    new_answer = letters[texts.index(correct_text)]

    return {
        **question,
        "options": new_options,
        "answer": new_answer,
    }


if __name__ == "__main__":
    questions = generate_questions(5)
    print(f"\nGenerated {len(questions)} questions:\n")
    for i, q in enumerate(questions, 1):
        print(f"Q{i}: {q['question']}")
        for letter, text in q["options"].items():
            marker = " <--" if letter == q["answer"] else ""
            print(f"  {letter}) {text}{marker}")
        print()
