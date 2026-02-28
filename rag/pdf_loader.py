"""
PDF Loader - Load and chunk the Discover Canada PDF for RAG.

Purpose: Read a PDF file and split it into manageable text chunks for embedding.
Inputs: PDF file path (defaults to config.PDF_PATH).
Outputs: A list of LangChain Document objects (chunked text with metadata).
Dependencies: config.py, pypdf, langchain-text-splitters.
"""

import os
import config
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Chunk configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Mock content for sandbox mode — covers key Discover Canada topics
_MOCK_DOCUMENTS_TEXT = [
    (
        "The capital of Canada is Ottawa. Ottawa is located in the province of Ontario, "
        "on the border with Quebec. The Parliament of Canada is located on Parliament Hill "
        "in Ottawa. The Peace Tower is one of its most recognizable features."
    ),
    (
        "Canada has ten provinces and three territories. The provinces are: Ontario, Quebec, "
        "Nova Scotia, New Brunswick, Manitoba, British Columbia, Prince Edward Island, "
        "Saskatchewan, Alberta, and Newfoundland and Labrador. The territories are: "
        "Yukon, Northwest Territories, and Nunavut."
    ),
    (
        "The Canadian Charter of Rights and Freedoms is part of the Constitution of Canada. "
        "It guarantees fundamental freedoms including freedom of conscience and religion, "
        "freedom of thought, belief, opinion, and expression, freedom of peaceful assembly, "
        "and freedom of association."
    ),
    (
        "Sir John A. Macdonald was the first Prime Minister of Canada. He served from 1867 "
        "to 1873 and again from 1878 to 1891. He was a key figure in Canadian Confederation "
        "and the building of the Canadian Pacific Railway."
    ),
    (
        "Canada became a country on July 1, 1867, through the British North America Act "
        "(now called the Constitution Act, 1867). This united three colonies: the Province "
        "of Canada (which became Ontario and Quebec), Nova Scotia, and New Brunswick."
    ),
    (
        "The three branches of government in Canada are: the Executive (led by the Prime "
        "Minister and Cabinet), the Legislative (the Parliament, consisting of the Senate "
        "and House of Commons), and the Judicial (the courts, led by the Supreme Court of Canada)."
    ),
    (
        "The Canadian flag features a red maple leaf on a white background with red bars on "
        "each side. It was officially adopted on February 15, 1965. The maple leaf has been "
        "a symbol of Canada since the 18th century."
    ),
    (
        "In Canada, citizens have the right to vote in federal, provincial, and municipal "
        "elections. Voting is a democratic right guaranteed by the Charter. Federal elections "
        "must be held at least every five years. Canada uses a first-past-the-post electoral system."
    ),
    (
        "The Royal Canadian Mounted Police (RCMP) is Canada's national police force. "
        "Founded in 1873 as the North-West Mounted Police, the RCMP is recognized worldwide "
        "by their iconic red serge uniform. They serve as the federal police force and "
        "also provide provincial and municipal policing in many areas."
    ),
    (
        "The War of 1812 was a defining moment in Canadian history. Canadian and British forces "
        "successfully defended Canada against American invasion. Key figures include Major-General "
        "Sir Isaac Brock and Tecumseh, a Shawnee chief who allied with the British. The war "
        "helped establish a sense of Canadian identity."
    ),
    (
        "Canada's official languages are English and French. The Official Languages Act of 1969 "
        "established both as equal official languages of the federal government. New Brunswick "
        "is the only officially bilingual province."
    ),
    (
        "The Canadian Constitution includes the Constitution Act of 1867 and the Constitution "
        "Act of 1982. The 1982 Act patriated the Constitution from Britain and included the "
        "Charter of Rights and Freedoms. The amending formula requires consent from Parliament "
        "and at least seven provinces representing 50% of the population."
    ),
    (
        "Aboriginal peoples in Canada include First Nations, Inuit, and Metis. They have lived "
        "in Canada for thousands of years before European contact. The Constitution recognizes "
        "and affirms existing Aboriginal and treaty rights."
    ),
    (
        "The responsibilities of Canadian citizenship include obeying the law, serving on a jury, "
        "voting in elections, helping others in the community, and protecting Canada's natural "
        "heritage and environment."
    ),
    (
        "Canada's economy is diverse and includes natural resources such as oil, gas, minerals, "
        "and timber. Key industries include manufacturing, technology, agriculture, and services. "
        "Canada is a major trading nation and a member of the G7."
    ),
    (
        "Remembrance Day is observed on November 11 in Canada. It honors the members of the "
        "armed forces who have served and sacrificed in wars and military operations. Canadians "
        "wear red poppies as a symbol of remembrance."
    ),
    (
        "The Governor General represents the Sovereign (King or Queen) in Canada and performs "
        "ceremonial duties including giving Royal Assent to bills passed by Parliament, "
        "reading the Speech from the Throne, and dissolving Parliament for elections."
    ),
    (
        "The House of Commons is the elected chamber of Parliament. Members of Parliament (MPs) "
        "are elected by the people in their constituencies. The political party with the most "
        "seats usually forms the government, and its leader becomes the Prime Minister."
    ),
    (
        "The Senate is the upper house of the Parliament of Canada. Senators are appointed by "
        "the Governor General on the advice of the Prime Minister. The Senate reviews and "
        "amends legislation passed by the House of Commons."
    ),
    (
        "Terry Fox is a Canadian hero who, after losing his leg to cancer, ran across Canada "
        "in 1980 in his Marathon of Hope to raise money for cancer research. Though he had to "
        "stop after 143 days, his legacy continues through the annual Terry Fox Run."
    ),
]


def load_pdf(pdf_path: str = None) -> list:
    """
    Load a PDF file and split it into text chunks.

    In sandbox mode, returns mock documents based on Discover Canada content.

    Args:
        pdf_path: Path to the PDF file. Defaults to config.PDF_PATH.

    Returns:
        A list of LangChain Document objects with page_content and metadata.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist (non-sandbox mode).
    """
    if pdf_path is None:
        pdf_path = config.PDF_PATH

    if config.is_sandbox():
        return _load_mock_documents()

    return _load_real_pdf(pdf_path)


def _load_mock_documents() -> list:
    """Generate mock Document objects for sandbox testing."""
    from langchain_core.documents import Document

    print("[Sandbox] Loading mock Discover Canada content...")
    documents = []
    for i, text in enumerate(_MOCK_DOCUMENTS_TEXT):
        doc = Document(
            page_content=text,
            metadata={"source": "discover_canada.pdf (mock)", "page": i + 1},
        )
        documents.append(doc)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    print(f"[Sandbox] Loaded {len(chunks)} text chunks from mock data.")
    return chunks


def _load_real_pdf(pdf_path: str) -> list:
    """Load and chunk a real PDF file."""
    from langchain_community.document_loaders import PyPDFLoader

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"PDF not found at '{pdf_path}'. "
            f"Please place your Discover Canada PDF in the data/ directory."
        )

    print(f"Loading PDF from: {pdf_path}")
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        print(f"Loaded {len(pages)} pages from PDF.")
    except Exception as e:
        raise RuntimeError(f"Failed to load PDF: {e}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)
    print(f"Split into {len(chunks)} text chunks.")
    return chunks


if __name__ == "__main__":
    docs = load_pdf()
    print(f"\nTotal chunks: {len(docs)}")
    if docs:
        print(f"First chunk preview: {docs[0].page_content[:100]}...")
        print(f"First chunk metadata: {docs[0].metadata}")
