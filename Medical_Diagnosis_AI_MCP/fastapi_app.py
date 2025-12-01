from fastapi import FastAPI
from pydantic import BaseModel
from tools.symptom_Extractor import extract_symptoms
from tools.diagonisis_tool import get_diagnosis
from tools.pubmed_fetcher import fetch_pubmed_articles_with_metadata
from tools.summarizer import summarize_text

app = FastAPI()
'''FastAPI is built on Pydantic models, and they give you several advantages:
- Automatic request parsing
- When you declare a BaseModel, FastAPI automatically reads the incoming JSON body and converts it into a Python object.
'''
class SymptomInput(BaseModel):
        description:str
    
@app.post("/diagnosis")

def diagnose_patient(data: SymptomInput):
    symptoms = extract_symptoms(data.description)
    diagnosis = get_diagnosis(symptoms)
    pubmed_raw = fetch_pubmed_articles_with_metadata(" ".join(symptoms))
    summary = summarize_text(pubmed_raw[:3000])

    return {
        "symptom": symptoms,
            "diagnosis": diagnosis,
            "pubmed_summary": summary
    }
    
    
