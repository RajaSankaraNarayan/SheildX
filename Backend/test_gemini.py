import httpx, asyncio, os, dotenv, json
from google import genai

dotenv.load_dotenv(r'..\fintech\fintech\.env')
gemini_key = os.getenv('GEMINI_API_KEY')

sys_prompt = 'You are Sentinel Voice AI. Output strictly JSON: {"language_code": "code", "text": "response"}'

client = genai.Client(api_key=gemini_key)
res = client.models.generate_content(
    model='gemini-3.5-flash',
    contents='Vanakkam',
    config=genai.types.GenerateContentConfig(
        system_instruction=sys_prompt,
        response_mime_type='application/json'
    )
)
print('RAW GEMINI:', res.text.encode('unicode_escape').decode())

try:
    data = json.loads(res.text)
    print('JSON PARSED:', data)
except Exception as e:
    print('JSON ERROR:', e)
