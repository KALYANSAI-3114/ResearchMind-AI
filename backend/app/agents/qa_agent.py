"""
Q&A Agent
Generate concise answers to questions based on retrieved context.
Uses LLM-based generation with Ollama (local, free) or OpenAI API (optional).
Implements proper RAG with retrieval + generation layer.
"""

import os
import re
import requests
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


def generate_answer(
    question: str,
    context: str,
    use_openai: bool = False,
    use_ollama: bool = True,
    max_length: int = 300
) -> str:
    """
    Generate a concise answer to a question based on context using LLM.
    
    This implements proper RAG: retrieval (done upstream) + generation (here).
    
    Args:
        question: The question to answer
        context: The relevant text context to answer from
        use_openai: Whether to use OpenAI API for generation
        use_ollama: Whether to use Ollama (local LLM, free)
        max_length: Maximum answer length in characters
    
    Returns:
        Generated answer string (LLM-generated, not just extracted)
    """
    return generate_answer_with_metadata(
        question=question,
        context=context,
        use_openai=use_openai,
        use_ollama=use_ollama,
        max_length=max_length
    )["answer"]


def generate_answer_with_metadata(
    question: str,
    context: str,
    use_openai: bool = False,
    use_ollama: bool = True,
    max_length: int = 300
) -> Dict[str, Any]:
    """
    Generate an answer and report which generation provider was used.

    provider values:
    - ollama: true local LLM generation
    - openai: true hosted LLM generation
    - fallback: extractive/synthetic fallback when no LLM is available
    """
    if not context or not question:
        return {
            "answer": "Could not generate answer - missing context or question.",
            "provider": "none",
            "model": None,
            "is_generative": False
        }
    
    # Try Ollama first (local, free, no API costs)
    if use_ollama:
        answer, model = _generate_with_ollama(question, context, max_length)
        if answer:
            return {
                "answer": _clean_generated_answer(answer, max_length),
                "provider": "ollama",
                "model": model,
                "is_generative": True
            }
    
    # Fall back to OpenAI if available
    if use_openai:
        answer, model = _generate_with_openai(question, context, max_length)
        if answer:
            return {
                "answer": _clean_generated_answer(answer, max_length),
                "provider": "openai",
                "model": model,
                "is_generative": True
            }
    
    # Last resort: synthesize a short answer from the retrieved evidence.
    return {
        "answer": _synthesize_fallback_answer(question, context, max_length),
        "provider": "fallback",
        "model": None,
        "is_generative": False
    }


def _generate_with_ollama(
    question: str,
    context: str,
    max_length: int = 300
) -> tuple[Optional[str], Optional[str]]:
    """
    Generate answer using Ollama (local LLM, free, no API costs).
    
    Ollama runs locally and supports:
    - Llama 2
    - Mistral
    - Neural Chat
    - Dolphin Mixtral
    - And many more
    
    Requires: ollama pull phi3:mini (or set OLLAMA_MODEL to your preferred model)
    """
    try:
        prompt = f"""You are a research paper assistant.

Answer ONLY using the provided context.

If the answer exists in the context:
- explain it clearly
- use technical accuracy
- keep answer concise

If the context does not contain the answer, say:
"The paper does not clearly mention this."

Keep the answer under {max_length} characters.

Context:
{context[:2000]}

Question:
{question}

Answer:
"""

        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        last_model = None

        for model in _ollama_model_candidates():
            last_model = model

            response = requests.post(
                ollama_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 80,
                        "num_ctx": 2048
                    },
                },
                timeout=120
            )

            if response.status_code != 200:
                print(f"Ollama model {model} failed with status {response.status_code}")
                continue

            result = response.json()
            answer = result.get("response", "").strip()

            if answer:
                if len(answer) > max_length:
                    answer = answer[:max_length].rsplit(" ", 1)[0] + "..."
                return answer, model

        return None, last_model
    
    except requests.exceptions.ConnectionError:
        print("Ollama not available. Install it from https://ollama.ai or use local installation")
        return None, None
    except Exception as e:
        print(f"Ollama generation failed: {str(e)}")
        return None, None


def _ollama_model_candidates() -> list:
    """Return configured Ollama model choices with local fallbacks."""
    preferred_model = os.getenv("OLLAMA_MODEL", "").strip()
    candidates = []

    if preferred_model:
        candidates.append(preferred_model)

    candidates.extend(["llama3:latest", "llama3", "phi3:mini"])

    unique_candidates = []
    for model in candidates:
        if model and model not in unique_candidates:
            unique_candidates.append(model)

    return unique_candidates


def _generate_with_openai(
    question: str,
    context: str,
    max_length: int = 300
) -> tuple[Optional[str], Optional[str]]:
    """
    Generate answer using OpenAI API.
    
    Requires OPENAI_API_KEY environment variable.
    Falls back gracefully if API unavailable or key missing.
    """
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OpenAI API key not found in OPENAI_API_KEY environment variable")
            return None, None
        
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        prompt = f"""Answer ONLY using the provided context.

If the answer exists in the context:
- explain it clearly
- use technical accuracy
- keep answer concise

If the context does not contain the answer, say:
"The paper does not clearly mention this."

Keep the answer under {max_length} characters.

Context:
{context[:2000]}

Question:
{question}

Answer:"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful research paper assistant. Answer from provided evidence only. Be concise, specific, and natural."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=150,
            timeout=30
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Truncate if needed
        if len(answer) > max_length:
            answer = answer[:max_length].rsplit(" ", 1)[0] + "..."
        
        return (answer, model) if answer else (None, model)
    
    except Exception as e:
        print(f"OpenAI generation failed: {str(e)}")
        return None, None


def _synthesize_fallback_answer(
    question: str,
    context: str,
    max_length: int = 300
) -> str:
    """
    Build a concise answer-shaped fallback from the best retrieved sentences.

    This is used only when no LLM provider is available. It avoids returning a
    raw chunk by selecting evidence and lightly framing it as an answer.
    """
    # Extract key terms from question
    question_keywords = _extract_keywords(question)
    
    # Find relevant sentences containing these keywords
    sentences = _split_into_sentences(context)
    relevant_sentences = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        # Score sentence based on keyword matches
        keyword_matches = sum(1 for kw in question_keywords if kw.lower() in sentence_lower)
        
        if keyword_matches > 0:
            relevant_sentences.append((sentence.strip(), keyword_matches))
    
    # Sort by relevance (keyword match count) and take top sentences
    relevant_sentences.sort(key=lambda x: x[1], reverse=True)
    
    if relevant_sentences:
        top_sentences = [s[0] for s in relevant_sentences[:2]]
        answer = _compose_answer_from_sentences(question, top_sentences)
    else:
        answer = "The retrieved paper context does not provide enough specific information to answer this question."
    
    # Limit to max_length
    if len(answer) > max_length:
        answer = answer[:max_length].rsplit(" ", 1)[0] + "..."
    
    return answer if answer else "Answer could not be extracted from context."


def _compose_answer_from_sentences(question: str, sentences: list) -> str:
    """Turn retrieved evidence sentences into a compact answer."""
    evidence = " ".join(_clean_sentence(sentence) for sentence in sentences if sentence.strip())
    evidence = re.sub(r"\s+", " ", evidence).strip()

    definition_answer = _compose_definition_answer(question, evidence)
    if definition_answer:
        return definition_answer

    question_lower = question.lower()
    if question_lower.startswith("what"):
        prefix = "According to the paper, "
    elif question_lower.startswith("how"):
        prefix = "The paper explains that "
    elif question_lower.startswith("why"):
        prefix = "The paper indicates that "
    else:
        prefix = "Based on the retrieved paper context, "

    if not evidence:
        return "The retrieved paper context does not provide enough specific information to answer this question."

    return prefix + evidence[0].lower() + evidence[1:]


def _compose_definition_answer(question: str, evidence: str) -> Optional[str]:
    """Create a short definition for questions like 'what is encoder'."""
    question_match = re.search(r"\bwhat\s+(?:is|are)\s+(?:an?|the)?\s*([a-zA-Z][\w-]*)", question.lower())
    if not question_match:
        return None

    term = question_match.group(1)
    term_pattern = re.escape(term)

    patterns = [
        rf"\b{term_pattern}\b\s+maps\s+([^.;]+?)\s+to\s+([^.;]+)",
        rf"\b{term_pattern}\b\s+converts\s+([^.;]+?)\s+into\s+([^.;]+)",
        rf"\b{term_pattern}\b\s+is composed of\s+([^.;]+)",
        rf"\b{term_pattern}\b\s+(?:is|are|refers to|means)\s+([^.;]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, evidence, flags=re.IGNORECASE)
        if not match:
            continue

        if "maps" in pattern:
            return f"The {term} maps {match.group(1).strip()} to {match.group(2).strip()}."
        if "converts" in pattern:
            return f"The {term} converts {match.group(1).strip()} into {match.group(2).strip()}."
        if "composed" in pattern:
            return f"The {term} is composed of {match.group(1).strip()}."

        definition = match.group(1).strip()
        return f"The {term} is {definition}."

    sentence_match = re.search(rf"[^.?!]*\b{term_pattern}\b[^.?!]*[.?!]", evidence, flags=re.IGNORECASE)
    if sentence_match:
        sentence = sentence_match.group(0).strip()
        return f"The {term} is described in the paper as follows: {sentence}"

    return None


def _clean_sentence(sentence: str) -> str:
    """Remove citation clutter and spacing artifacts from extracted evidence."""
    sentence = re.sub(r"\[[0-9,\s-]+\]", "", sentence)
    sentence = re.sub(r"\([A-Z][A-Za-z-]+ et al\.,?\s*\d{4}\)", "", sentence)
    sentence = re.sub(r"\([^)]{15,}\)", "", sentence)
    sentence = re.sub(r"\s+", " ", sentence)
    return sentence.strip()


def _clean_generated_answer(answer: str, max_length: int) -> str:
    """Keep provider answers concise and remove prompt/format artifacts."""
    answer = answer.strip()
    answer = re.sub(r"^(answer|response)\s*:\s*", "", answer, flags=re.IGNORECASE)
    answer = re.sub(r"\s+", " ", answer)

    sentences = _split_into_sentences(answer)
    if len(sentences) > 2:
        answer = " ".join(sentences[:2])

    if len(answer) > max_length:
        answer = answer[:max_length].rsplit(" ", 1)[0] + "..."

    return answer


def _extract_keywords(text: str, limit: int = 10) -> list:
    """
    Extract important keywords from text.
    Prioritizes nouns and technical terms.
    """
    # Remove common words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "is", "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should", "may",
        "might", "can", "what", "which", "who", "where", "when", "why", "how",
        "this", "that", "these", "those", "i", "you", "he", "she", "it", "we",
        "they", "by", "as", "with", "from", "up", "about", "out", "if", "so"
    }
    
    # Split into words and filter
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out stop words and short words
    keywords = [
        w for w in words
        if w not in stop_words and len(w) > 3
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    
    return unique_keywords[:limit]


def _split_into_sentences(text: str) -> list:
    """
    Split text into sentences.
    Handles common abbreviations and edge cases.
    """
    # Replace common abbreviations to avoid splitting on them
    text = text.replace("Dr.", "Dr_")
    text = text.replace("Prof.", "Prof_")
    text = text.replace("Inc.", "Inc_")
    text = text.replace("Ltd.", "Ltd_")
    text = text.replace("et al.", "et_al_")
    text = text.replace("e.g.", "e_g_")
    text = text.replace("i.e.", "i_e_")
    
    # Split on sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Restore abbreviations and clean up
    sentences = [s.replace("Dr_", "Dr.").replace("Prof_", "Prof.")
                 .replace("Inc_", "Inc.").replace("Ltd_", "Ltd.")
                 .replace("et_al_", "et al.").replace("e_g_", "e.g.")
                 .replace("i_e_", "i.e.").strip()
                 for s in sentences if s.strip()]
    
    return sentences
