import re

def extract_symptoms(text: str) -> list[str]:
    # Regular expression pattern to match common symptom phrases
    symptom_patterns = re.findall(r'\b(headache|fever|cough|fatigue|nausea|dizziness|pain|swelling|rash|chills|sore throat|shortness of breath|vomiting|diarrhea|muscle aches|joint pain|loss of taste or smell|painful|severe|mild|chronic)\b', text.lower())
    return list(set(symptom_patterns))

    