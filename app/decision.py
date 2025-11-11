# app/decision.py
from app.embedding import search_vectorstore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
from app.config import settings

# 🔄 Generalized system prompt
system_prompt = """
You are an AI assistant that helps users find specific information from documents like policies, contracts, HR guidelines, travel rules, or emails.

Your job is to:
- Answer the user's question using ONLY the information present in the provided documents.
- Extract the exact relevant details, sentences, or clauses that answer the question.
- Be specific and detailed - provide the actual information, not just "the document mentions X".
- If the document doesn't contain the answer, say "Information not found in the document".
- Quote relevant parts of the document to support your answer.

Respond in this strict JSON format:
{{
  "decision": "answered" or "not_found" or "insufficient information",
  "amount": number or null,
  "justification": "Detailed answer with specific information from the document. Include actual details, numbers, lists, requirements, etc. - not just 'the document says X'.",
  "clauses_used": [
    {{
      "text": "exact sentence or clause from the document that supports the answer",
      "page": "page number or section (if available)"
    }}
  ]
}}

Example:
Question: "What are the password requirements?"
BAD: "The document outlines password requirements."
GOOD: "Passwords must be at least 8 characters long, contain uppercase, lowercase, numbers, and special characters. They must be changed every 90 days."
"""

def evaluate_with_llm(query: str, vectorstore):
    relevant_docs = search_vectorstore(vectorstore, query, k=8)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Documents:\n\n{context}\n\nQuery:\n{query}")
    ])

    model = ChatGroq(
        model=settings.model_name,
        api_key=settings.groq_api_key
    )

    chain = prompt | model | JsonOutputParser()

    try:
        result = chain.invoke({"context": context, "query": query})
        return result
    except Exception as e:
        return {
            "decision": "error",
            "amount": None,
            "justification": str(e),
            "clauses_used": []
        }
