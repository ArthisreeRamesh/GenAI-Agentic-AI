import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def summarize_text(text: str) -> str:
            prompt = f"Summarize the following medical abstract, highlighting the key objectives, methods, results, and conclusions in simple and precise language:\n\n{text}"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical research summarizer for text."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()