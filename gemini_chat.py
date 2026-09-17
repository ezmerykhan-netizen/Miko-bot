import asyncio
import random
from google import genai
from config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    GEMINI_TYPING_DELAY_MIN, GEMINI_TYPING_DELAY_MAX
)
from texts import GEMINI_SYSTEM_PROMPT

client = genai.Client(api_key=GEMINI_API_KEY)
_chat_memory = {}


async def get_gemini_reply(user_message, chat_id):
    if not user_message or not user_message.strip():
        return None

    delay = random.uniform(GEMINI_TYPING_DELAY_MIN, GEMINI_TYPING_DELAY_MAX)
    await asyncio.sleep(delay)

    history = _chat_memory.get(chat_id, [])
    history.append(f"کاربر: {user_message}")
    history = history[-6:]

    prompt = GEMINI_SYSTEM_PROMPT + "\n\n" + "\n".join(history) + "\nربات:"

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        reply = (response.text or "").strip()
        if not reply:
            return None
        history.append(f"ربات: {reply}")
        _chat_memory[chat_id] = history[-6:]
        return reply[:120]
    except Exception as e:
        print(f"[GEMINI] خطا: {e}")
        return None
