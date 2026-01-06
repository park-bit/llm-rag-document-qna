# backend/llm.py
import os
import logging
from groq import Groq
print(">>> USING backend.llm.generate FROM", __file__)

logger = logging.getLogger("llm")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or "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"


if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in environment")

client = Groq(api_key=GROQ_API_KEY)

MODEL = "llama-3.1-8b-instant"


def generate(prompt: str, retrieved_texts=None) -> str:
    """
    Generate text using Groq LLM.
    Input: prompt string
    Optional: retrieved_texts - list of context strings (passed by callers)
    Output: plain text response
    """
    try:
        # Build messages; include provided retrieved_texts as additional context when available.
        messages = [
            {"role": "system", "content": "You are a precise document analysis assistant."},
        ]

        if retrieved_texts:
            # If retrieved_texts is a list, join; otherwise coerce to str
            if isinstance(retrieved_texts, (list, tuple)):
                context_block = "\n\n".join(str(t) for t in retrieved_texts)
            else:
                context_block = str(retrieved_texts)

            # Add the context as a user message before the prompt so model sees it.
            messages.append({"role": "user", "content": f"Context:\n{context_block}"})

        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )

        content = response.choices[0].message.content
        if not content:
            return ""

        return content.strip()

    except Exception:
        logger.exception("Groq generation failed")
        return ""
