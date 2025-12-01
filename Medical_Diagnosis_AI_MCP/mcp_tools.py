from fastmcp import FastMCP
from pydantic import BaseModel
from tools.symptom_Extractor import extract_symptoms
from tools.diagonisis_tool import get_diagnosis
from tools.pubmed_fetcher import fetch_pubmed_articles_with_metadata
from tools.summarizer import summarize_text

mcp = FastMCP("Medical dagonisis custom AI MCP")

@mcp.tool()

def pseudo_doc_analyze_patient(data: BaseModel):
    symptoms = extract_symptoms(data.description)
    diagnosis = get_diagnosis(symptoms)
    pubmed_raw = fetch_pubmed_articles_with_metadata(" ".join(symptoms))
    summary = summarize_text(pubmed_raw[:3000])

    return {
        "symptom": symptoms,
            "diagnosis": diagnosis,
            "pubmed_summary": summary
    }

if __name__ == "__main__":
    mcp.run()
