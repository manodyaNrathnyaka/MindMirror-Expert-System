# """
# LLM Explainer module

import os
from typing import List, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from openai import OpenAI


# Load API key safely
_API_KEY = os.getenv("OPENAI_API_KEY")
_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

if not _API_KEY:
  
    client = None
else:
    client = OpenAI(api_key=_API_KEY)


def generate_llm_explanation(test_name: str, qa_pairs: List[Dict[str, str]], result_data: Dict) -> str:
  
    formatted_qna = "\n".join(
        [f"- {pair.get('question', '')} → {pair.get('answer', '')}" for pair in qa_pairs]
    )

    percentage = result_data.get("percentage")
    result_label = result_data.get("result", "No result")
    alternative = result_data.get("alternative", "N/A")

    prompt = f"""
You are a kind, encouraging psychologist.
Never be robotic or clinical.

TEST TYPE: {test_name}

USER ANSWERS:
{formatted_qna}

RESULT FROM EXPERT SYSTEM:
→ Outcome: {result_label}
→ Probability: {percentage:.2f}%
→ Other possible explanation: {alternative}

Write a short, friendly explanation:
1. Explain what this result means in simple words.
2. Tell WHY the answers indicate that result.
3. Give 2 gentle alternative interpretations (ex: lack of sleep / burnout).
4. Give 3 tiny improvement actions the user can try today.
Tone: warm, supportive, motivational, short paragraphs.
"""

    # Ensure client is available
    if client is None:
        raise RuntimeError("OPENAI_API_KEY not set. Configure it in the environment or .env file to enable LLM explanations.")

    # Call the chat completion endpoint (model configurable).
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": "You speak with emotional intelligence and kindness."},
            {"role": "user", "content": prompt},
        ],
    )

    # Extract assistant text robustly to handle different SDK/response shapes.
    try:
        choice = response.choices[0]
    except Exception:
        raise RuntimeError(f"Unexpected response shape from LLM: {response}")

    # Try common access patterns in order.
    # 1) new-style object with `.message.content`
    try:
        msg = getattr(choice, 'message', None)
        if msg is not None:
            # msg might be a dict-like or an object
            try:
                return msg['content']
            except Exception:
                try:
                    return msg.content
                except Exception:
                    # last resort
                    pass
    except Exception:
        pass

    # 2) older/alternate pattern: message is dict under .message
    try:
        m = choice.message
        try:
            return m['content']
        except Exception:
            try:
                return m.content
            except Exception:
                pass
    except Exception:
        pass

    # 3) fallback to .text or direct attribute
    text = getattr(choice, 'text', None)
    if text:
        return text

    # 4) last resort: stringify the whole response
    return str(response)


# Simple availability flag for UIs
AVAILABLE = client is not None

# from openai import OpenAI

# client = OpenAI()

# models = client.models.list()

# for m in models.data:
#     print(m.id)
