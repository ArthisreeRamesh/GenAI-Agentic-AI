import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def get_diagnosis(symptoms: list[str]) -> str:
            prompt = f"Patient has symptoms: {', '.join(symptoms)}. Based on the given symptoms, suggest possible medical conditions that could be the cause. For each condition, explain why it might occur, outline possible treatment options or cures, and recommend the type of medical specialist I should consult for confirmation and proper care."
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful medical assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
