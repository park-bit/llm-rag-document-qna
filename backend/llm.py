import os
import logging
from groq import Groq
print(">>> USING backend.llm.generate FROM", __file__)

logger = logging.getLogger("llm")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


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

        messages = [
            {"role": "system", "content": "You are a precise document analysis assistant."},
        ]

        if retrieved_texts:
            if isinstance(retrieved_texts, (list, tuple)):
                context_block = "\n\n".join(str(t) for t in retrieved_texts)
            else:
                context_block = str(retrieved_texts)

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
