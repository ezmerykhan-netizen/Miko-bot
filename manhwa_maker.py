from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)

MANHWA_PROMPT = """تو یه نویسنده مانهوا هستی. داستان زیر رو بخون و به صحنه‌های تصویری تقسیم کن.

برای هر صحنه:
1. شماره صحنه
2. توضیح تصویر (به انگلیسی، برای AI image generator مثل Flux یا Imagen)
3. دیالوگ (به فارسی)
4. حس و حال شخصیت‌ها

خروجی رو به صورت JSON بده:
{{"scenes": [{{"scene": 1, "image_prompt": "...", "dialogue": "...", "mood": "..."}}]}}

داستان:
{story}"""


async def story_to_manhwa(story):
    prompt = MANHWA_PROMPT.format(story=story)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"خطا: {e}"
