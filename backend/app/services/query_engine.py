"""
Query engine service for RAG-based question answering
"""
from typing import Dict, Any, List, Optional
import time
# Ganti import ini:
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI # <-- GANTI INI
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
from app.services.vector_store import VectorStore
from app.services.metrics_calculator import MetricsCalculator
from sqlalchemy.orm import Session


class QueryEngine:
    """RAG-based query engine for fund analysis"""

    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStore()
        self.metrics_calculator = MetricsCalculator(db)
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM"""
        # Ganti logika inisialisasi
        if settings.GOOGLE_API_KEY: # <-- GANTI KONDISI
            return ChatGoogleGenerativeAI( # <-- GANTI INISIALISASI
                model=settings.GEMINI_MODEL, # <-- GANTI NAMA MODEL
                temperature=0,
                google_api_key=settings.GOOGLE_API_KEY, # <-- GANTI NAMA API KEY
                convert_system_message_to_human=True
            )
        elif settings.OPENAI_API_KEY: # <-- KONDISI CADANGAN (OPSIONAL)
            # Fallback ke OpenAI jika Google API key tidak ada
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            # Fallback ke local LLM
            return Ollama(model="llama2")

    async def process_query(
        self,
        query: str,
        fund_id: Optional[int] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query using RAG

        Args:
            query: User question
            fund_id: Optional fund ID for context
            conversation_history: Previous conversation messages

        Returns:
            Response with answer, sources, and metrics
        """
        start_time = time.time()

        # Step 1: Classify query intent
        intent = await self._classify_intent(query)

        # Step 2: Retrieve relevant context from vector store
        filter_metadata = {"fund_id": fund_id} if fund_id else None
        relevant_docs = await self.vector_store.similarity_search(
            query=query,
            k=settings.TOP_K_RESULTS,
            filter_metadata=filter_metadata
        )

        # Step 3: Calculate metrics if needed
        metrics = None
        if intent == "calculation" and fund_id:
            metrics = self.metrics_calculator.calculate_all_metrics(fund_id)

        # Step 4: Generate response using LLM
        answer = await self._generate_response(
            query=query,
            context=relevant_docs,
            metrics=metrics,
            conversation_history=conversation_history or []
        )

        processing_time = time.time() - start_time

        return {
            "answer": answer,
            "sources": [
                {
                    "content": doc["content"],
                    "metadata": {
                        k: v for k, v in doc.items()
                        if k not in ["content", "score"]
                    },
                    "score": doc.get("score")
                }
                for doc in relevant_docs
            ],
            "metrics": metrics,
            "processing_time": round(processing_time, 2)
        }

    async def _classify_intent(self, query: str) -> str:
        """
        Classify query intent

        Returns:
            'calculation', 'definition', 'retrieval', or 'general'
        """
        query_lower = query.lower()

        # Calculation keywords
        calc_keywords = [
            "calculate", "what is the", "current", "dpi", "irr", "tvpi",
            "rvpi", "pic", "paid-in capital", "return", "performance"
        ]
        if any(keyword in query_lower for keyword in calc_keywords):
            return "calculation"

        # Definition keywords
        def_keywords = [
            "what does", "mean", "define", "explain", "definition",
            "what is a", "what are"
        ]
        if any(keyword in query_lower for keyword in def_keywords):
            return "definition"

        # Retrieval keywords
        ret_keywords = [
            "show me", "list", "all", "find", "search", "when",
            "how many", "which"
        ]
        if any(keyword in query_lower for keyword in ret_keywords):
            return "retrieval"

        return "general"

    async def _generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        metrics: Optional[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Generate response using LLM"""

        # Helper function to escape curly braces
        def escape_curly_braces(text: str) -> str:
            return text.replace("{", "{{").replace("}", "}}")

        # Build context string and escape curly braces
        context_str = "\n\n".join([
            f"[Source {i+1}]\n{escape_curly_braces(doc['content'])}"
            for i, doc in enumerate(context[:3])  # Use top 3 sources
        ])

        metrics_str = ""
        if metrics:
            metrics_str = "\n\nAvailable Metrics:\n"
            for key, value in metrics.items():
                if value is not None:
                    safe_value = escape_curly_braces(str(value))
                    metrics_str += f"- {key.upper()}: {safe_value}\n"

        history_str = ""
        if conversation_history:
            history_str = "\n\nPrevious Conversation:\n"
            for msg in conversation_history[-3:]:
                safe_content = escape_curly_braces(msg['content'])
                history_str += f"{msg['role']}: {safe_content}\n"

        # --- PROMPT SISTEM YANG DIPERBAIKI SESUAI CALCULATIONS.md ---
        # Siapkan nilai-nilai dari metrics untuk dimasukkan ke prompt
        total_distributions_val = metrics.get("total_distributions", 0) if metrics else 0
        pic_val = metrics.get("pic", 0) if metrics else 0
        dpi_val = metrics.get("dpi", 0) if metrics else 0

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a financial analyst assistant specializing in private equity fund performance.

Your role:
- Answer questions about fund performance using provided context and pre-calculated metrics
- Explain complex financial terms in simple language
- Always cite your sources from the provided documents

When citing sources:
- **IMPORTANT: Do NOT use labels like [Source 1], [Source 2], etc. in your final response.**
- If you need to reference information from the documents, you can say things like "Based on the fund's performance report..." or "According to the transaction data...".
- If the user asks for specific details from the document, you can refer to the general context provided.

When calculating or explaining metrics:
- **CRITICAL: Use ONLY the pre-calculated metrics provided by the system:**
  - Total Distributions (Gross): {total_distributions_val}
  - Paid-In Capital (PIC) (Net): {pic_val} (Calculated as Total Capital Calls minus Total Adjustments)
  - DPI: {dpi_val} (Calculated as Total Distributions / PIC)
- **Do NOT re-calculate these values from individual transactions unless explicitly asked to show the breakdown from raw data.**
- Show your work step-by-step using the pre-calculated values.
- Explain any assumptions made based on the pre-calculated data.

Format your responses for maximum clarity and readability:
- Use clear headings (e.g., "1. Explanation of DPI", "2. Calculation Steps")
- Use bullet points for lists
- **CRITICAL: NEVER use LaTeX, Markdown math blocks, or any mathematical formatting like $$...$$, \\frac, \\text, \\mathbf, etc.**
- **ALWAYS use standard plain text with mathematical symbols: `=`, `-`, `+`, `/`, `*`. For example: `DPI = 4000000 / 10400000`**
- **Ensure there is a blank line (\\n\\n) between paragraphs and major sections.**
- Bold important final numbers using **number** (this is standard Markdown for bold text).
- Provide context for metrics.
- Keep explanations concise but thorough.

Important Calculation Rule (from CALCULATIONS.md):
- DPI is calculated as Cumulative Distributions (Gross) divided by Paid-In Capital (Net).
- Paid-In Capital (Net) is calculated as Total Capital Calls minus Total Adjustments.
- Distributions are taken at their gross amount, without subtracting recalls for this specific DPI calculation unless specified otherwise by the user's question.
"""),
            ("user", """Context from documents:
{context}
{metrics}
{history}

Question: {query}

Please provide a helpful answer based on the context and metrics provided, using the pre-calculated values.""")
        ])
        # --- AKHIR PROMPT SISTEM YANG DIPERBAIKI ---

        # Generate response using the updated prompt
        messages = prompt.format_messages(
            context=context_str,
            metrics=metrics_str,
            history=history_str,
            query=query
        )

        try:
            response = self.llm.invoke(messages)
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            return f"I apologize, but I encountered an error generating a response: {str(e)}"


