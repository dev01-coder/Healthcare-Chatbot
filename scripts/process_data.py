"""
Healthcare RAG Bot - Data Processor
Cleans and chunks all raw data into documents ready for embedding.
Run: python scripts/process_data.py
"""

import json
import csv
import re
import os
from pathlib import Path
from typing import List, Dict

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MEDICAL_DISCLAIMER = (
    "\n\n⚠️ This information is for educational purposes only. "
    "Always consult a qualified healthcare professional for medical advice, "
    "diagnosis, or treatment."
)


def clean_text(text: str) -> str:
    """Remove HTML tags, extra spaces, fix encoding."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def chunk_text(text: str, max_chars: int = 600, overlap: int = 80) -> List[str]:
    """Split long text into overlapping chunks."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        # Try to break at sentence boundary
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary > start + overlap:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if len(c) > 50]


def process_sample_qa() -> List[Dict]:
    """Process the built-in sample Q&A data."""
    path = RAW_DIR / "sample_qa.json"
    if not path.exists():
        return []

    print("Processing sample Q&A data...")
    docs = []
    with open(path) as f:
        data = json.load(f)

    for item in data:
        q = clean_text(item.get("question", ""))
        a = clean_text(item.get("answer", ""))
        if q and a:
            text = f"Question: {q}\n\nAnswer: {a}{MEDICAL_DISCLAIMER}"
            docs.append({
                "text": text,
                "source": "Healthcare Q&A",
                "category": "general",
                "question": q
            })

    print(f"   {len(docs)} documents from sample Q&A")
    return docs


def process_medquad_csv() -> List[Dict]:
    """Process MedQuAD CSV dataset (47K+ medical Q&A pairs from NIH)."""
    path = RAW_DIR / "medquad.csv"
    if not path.exists():
        print("   medquad.csv not found — skipping")
        return []

    print("Processing MedQuAD dataset...")
    docs = []
    skipped = 0
    MAX_RECORDS = 8000  # Limit for laptop-friendly indexing time (~30 min)
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= MAX_RECORDS:
                    print(f"   (capped at {MAX_RECORDS} records for laptop performance)")
                    break

                q = clean_text(str(row.get("question", "")))
                a = clean_text(str(row.get("answer", "")))
                focus = row.get("focus_area", "Disease")

                if not q or not a or len(a) < 30:
                    skipped += 1
                    continue

                # Chunk long answers for better retrieval
                chunks = chunk_text(a)
                for chunk in chunks:
                    docs.append({
                        "text": f"Question: {q}\n\nAnswer: {chunk}",
                        "source": "MedQuAD (NIH)",
                        "category": focus.lower() if focus else "disease",
                        "question": q
                    })

    except Exception as e:
        print(f"   Error reading medquad.csv: {e}")

    print(f"   {len(docs)} documents from MedQuAD (skipped {skipped} empty/short)")
    return docs


def process_disease_symptom() -> List[Dict]:
    """Process disease-symptom CSV."""
    path = RAW_DIR / "disease_symptom.csv"
    if not path.exists():
        return []

    print("Processing disease-symptom data...")
    docs = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            diseases = {}
            for row in reader:
                disease = clean_text(str(row.get("Disease", row.get("disease", ""))))
                symptom = clean_text(str(row.get("Symptom", row.get("symptom", ""))))
                if disease and symptom:
                    diseases.setdefault(disease, []).append(symptom)

        for disease, symptoms in diseases.items():
            symptom_list = ", ".join(symptoms[:10])
            text = (
                f"Disease: {disease}\n\n"
                f"Common symptoms of {disease} include: {symptom_list}.\n\n"
                f"If you experience these symptoms, consult a healthcare provider for proper diagnosis."
                f"{MEDICAL_DISCLAIMER}"
            )
            docs.append({
                "text": text,
                "source": "Disease-Symptom Database",
                "category": "symptoms",
                "question": f"What are the symptoms of {disease}?"
            })

    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    print(f"   {len(docs)} documents from disease-symptom data")
    return docs


def add_static_medical_knowledge() -> List[Dict]:
    """Add hand-crafted high-quality medical knowledge."""
    print("Adding static medical knowledge base...")

    knowledge = [
        {
            "topic": "Emergency Signs",
            "category": "emergency",
            "content": """MEDICAL EMERGENCIES - Seek immediate help for:
            
Heart Attack: Chest pain/pressure, pain in arm/jaw/neck, shortness of breath, cold sweat, nausea.
Stroke: Face drooping, Arm weakness, Speech difficulty (FAST). Sudden severe headache.
Severe Allergic Reaction (Anaphylaxis): Throat swelling, difficulty breathing, hives, rapid heartbeat.
Difficulty Breathing: Severe shortness of breath, blue lips or fingernails.
Severe Bleeding: Uncontrolled bleeding that doesn't stop.
Loss of Consciousness: Person won't wake up or is unresponsive.
Seizure: Convulsions, especially first-time or prolonged.
Overdose: Suspected drug or medication overdose.

ALWAYS call your local emergency services immediately for these conditions."""
        },
        {
            "topic": "Mental Health Crisis",
            "category": "mental_health",
            "content": """Mental Health Support Resources:

If you are having thoughts of suicide or self-harm, please reach out immediately:
- Call your local crisis helpline
- Reach out to a trusted friend or family member
- Go to the nearest hospital emergency room

Depression symptoms: Persistent sadness, loss of interest, sleep changes, hopelessness, fatigue.
Anxiety symptoms: Excessive worry, restlessness, rapid heartbeat, difficulty concentrating.
These are medical conditions — not signs of weakness. Help is available.

For non-emergency mental health support, consult a psychiatrist or psychologist.
You are not alone."""
        },
        {
            "topic": "Medication Safety",
            "category": "medication",
            "content": """Medication Safety Guidelines:

1. Always take medications as prescribed by your doctor
2. Do not share prescription medications with others
3. Never stop a medication suddenly without consulting your doctor
4. Store medications properly (away from heat, light, moisture)
5. Check expiry dates before taking any medication

Common OTC medications:
- Paracetamol (Acetaminophen): Fever and mild pain. Max 4g/day for adults.
- Ibuprofen: Pain and inflammation. Take with food. Avoid on empty stomach.
- ORS (Oral Rehydration Salts): For dehydration from diarrhea or vomiting.
- Antacids: For heartburn and indigestion.

ALWAYS consult a pharmacist or doctor before starting new medications.
Inform your doctor about all medications and supplements you take."""
        },
        {
            "topic": "Preventive Health",
            "category": "prevention",
            "content": """Preventive Health - Key Recommendations:

Vaccinations (Recommended Schedule):
- BCG (tuberculosis) - at birth
- Polio drops - multiple doses
- DPT-HepB-Hib - at 6, 10, 14 weeks  
- Measles vaccine - 9 months and 15 months
- Typhoid, Hepatitis A - recommended for adults

Health Screenings:
- Blood pressure: Check every 1-2 years (more often if hypertensive)
- Blood sugar: Screen adults over 45 or overweight
- Cholesterol: Every 4-6 years starting at age 20
- Eye exam: Every 1-2 years

Healthy Habits:
- 30 minutes moderate exercise, 5 days/week
- 5+ servings fruits and vegetables daily
- 7-9 hours sleep per night
- Avoid smoking and limit alcohol
- Wash hands frequently (20+ seconds with soap)"""
        },
        {
            "topic": "Common Infectious Diseases",
            "category": "regional",
            "content": """Common Infectious Diseases and Management:

1. Dengue Fever: High fever, severe headache, eye pain, joint pain, rash.
   - Prevention: Eliminate standing water, use mosquito repellent
   - Seek immediate medical care for dengue symptoms

2. Typhoid: Sustained high fever, abdominal pain, headache, weakness.
   - Prevention: Clean water, proper sanitation, typhoid vaccination
   - Requires antibiotic treatment - consult doctor

3. Hepatitis B & C: Often no symptoms. Causes liver damage over time.
   - Hep B: Vaccine available
   - Hep C: Get tested regularly

4. Malaria: Fever, chills, sweating, headache (cyclical pattern).
   - Common in tropical areas and after monsoon
   - Seek immediate medical testing and treatment

5. Tuberculosis (TB): Persistent cough >3 weeks, blood in sputum, weight loss, night sweats.
   - Free diagnosis and treatment available at government hospitals
   - Don't ignore symptoms

6. Diabetes: Very prevalent worldwide. Get blood sugar tested regularly."""
        },
        {
            "topic": "Diabetes Management",
            "category": "chronic_disease",
            "content": """Diabetes Management Guide:

Types:
- Type 1: Autoimmune, requires insulin injections
- Type 2: Most common (90%), linked to lifestyle, managed with diet/exercise/medication

Blood Sugar Targets:
- Fasting: 80-130 mg/dL
- 2 hours after meals: <180 mg/dL
- HbA1c: <7% (check every 3 months)

Daily Management:
1. Take medications as prescribed (metformin, insulin, etc.)
2. Monitor blood sugar regularly
3. Eat balanced meals (limit white rice, sugary drinks, refined flour)
4. Walk 30 minutes daily
5. Check feet daily for sores
6. Keep emergency sugar/glucose tablets

Complications if uncontrolled:
- Heart disease, stroke, kidney failure, blindness, nerve damage, amputations

Test blood sugar at least once a year if over 35 or overweight."""
        },
        {
            "topic": "Heart Disease Prevention",
            "category": "prevention",
            "content": """Heart Disease Prevention:

Risk Factors:
- High blood pressure, high cholesterol, diabetes, smoking, obesity, family history, sedentary lifestyle

Prevention Steps:
1. Don't smoke (biggest modifiable risk factor)
2. Exercise 150 minutes per week (30 min, 5 days/week)
3. Eat heart-healthy: fruits, vegetables, whole grains, fish, nuts
4. Reduce salt intake (<5g/day)
5. Control blood pressure (<120/80 mmHg)
6. Manage cholesterol (LDL <100 mg/dL)
7. Maintain healthy weight (BMI 18.5-24.9)
8. Limit alcohol
9. Manage stress
10. Regular health checkups

Warning Signs of Heart Attack:
- Chest pain/pressure, pain in arm/jaw/neck, shortness of breath, cold sweat, nausea
CALL YOUR LOCAL EMERGENCY NUMBER IMMEDIATELY — every minute counts

Heart disease is the #1 killer worldwide. Prevention is better than cure."""
        },
        {
            "topic": "Cancer Awareness",
            "category": "prevention",
            "content": """Cancer Warning Signs (7 Early Signs):

1. Unexplained weight loss (10+ pounds without trying)
2. Persistent fatigue not relieved by rest
3. Unusual bleeding or discharge
4. Thickening or lump in breast, testicle, or elsewhere
5. Indigestion or difficulty swallowing
6. Persistent cough or hoarseness
7. Changes in bowel or bladder habits

Most Common Cancers:
- Breast cancer (most common in women — self-examine monthly)
- Lung cancer (strongly linked to smoking)
- Colorectal cancer (screening after age 45)
- Oral cancer (linked to tobacco use)

Prevention:
- Don't use tobacco in any form
- Protect from sun (use sunscreen)
- Eat fruits and vegetables
- Maintain healthy weight
- Regular screenings and vaccinations (HPV, Hep B)

Early detection dramatically improves survival rates."""
        },
        {
            "topic": "Children's Health",
            "category": "pediatrics",
            "content": """Common Childhood Conditions:

Fever in Children:
- Normal: 97-99.9F (36.1-37.7C)
- Fever: 100.4F (38C) or higher
- Give paracetamol (10-15mg/kg every 4-6 hours)
- Seek care if: under 3 months old, fever >104F, seizures, lethargy, rash

Diarrhea and Dehydration:
- Give ORS (Oral Rehydration Salts) — most important treatment
- Continue breastfeeding and regular food
- Seek care if: blood in stool, sunken eyes, no tears, dry mouth

Common Childhood Vaccines (Recommended Schedule):
- BCG: at birth
- Polio drops: at birth + multiple doses
- DPT-HepB-Hib: 6, 10, 14 weeks
- Measles: 9 and 15 months
- Pneumococcal and Rotavirus: recommended

When to See a Doctor:
- Difficulty breathing, persistent vomiting, high fever, seizures, unusual drowsiness, refusal to eat/drink"""
        },
        {
            "topic": "Women's Health",
            "category": "womens_health",
            "content": """Key Women's Health Topics:

Menstrual Health:
- Normal cycle: 21-35 days, period lasts 3-7 days
- Heavy bleeding (soaking pad every hour), severe pain, or irregular cycles need medical evaluation

Breast Cancer Screening:
- Self-examination: monthly, 7-10 days after period starts
- Clinical exam: annually after age 30
- Mammogram: every 1-2 years after age 40
- Breast cancer is the most common cancer in women worldwide — regular self-examination is important

Prenatal Care:
- Start prenatal vitamins (folic acid) before conception
- Regular checkups throughout pregnancy
- Watch for warning signs: severe headache, vision changes, heavy bleeding, severe abdominal pain

Common Gynecological Issues:
- PCOS (Polycystic Ovary Syndrome): irregular periods, weight gain, acne, excess hair growth
- UTIs: frequent burning urination — drink water, see doctor for antibiotics
- Yeast infections: itching, discharge — treatable with antifungal medication"""
        },
        {
            "topic": "Elderly Health",
            "category": "geriatrics",
            "content": """Health Considerations for Older Adults:

Common Conditions:
- Hypertension (most common — monitor regularly)
- Arthritis (joint pain, stiffness — stay active, maintain healthy weight)
- Osteoporosis (weak bones — calcium, vitamin D, weight-bearing exercise)
- Dementia/Alzheimer's (memory loss, confusion — early diagnosis important)

Preventive Measures:
- Annual health checkups
- Regular blood pressure, blood sugar, cholesterol monitoring
- Fall prevention: remove tripping hazards, good lighting, grab bars
- Stay socially active
- Exercise regularly (walking, tai chi)
- Maintain healthy diet
- Keep vaccinations up to date (flu, pneumonia)

Medication Management:
- Keep a list of all medications
- Use pill organizers
- Don't mix medications without doctor's advice
- Report side effects to doctor immediately

When to Seek Emergency Care:
- Chest pain, stroke symptoms, severe falls, difficulty breathing, confusion"""
        },
    ]

    docs = []
    for item in knowledge:
        docs.append({
            "text": item["content"] + MEDICAL_DISCLAIMER,
            "source": "Curated Medical Knowledge Base",
            "category": item["category"],
            "question": f"Information about {item['topic']}"
        })

    print(f"   {len(docs)} static knowledge documents")
    return docs


def main():
    print("=" * 60)
    print("Healthcare RAG Bot - Data Processor")
    print("=" * 60)

    all_docs = []
    all_docs.extend(process_sample_qa())
    all_docs.extend(process_medquad_csv())
    all_docs.extend(process_disease_symptom())
    all_docs.extend(add_static_medical_knowledge())

    # Save processed docs
    output_path = PROCESSED_DIR / "all_documents.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Total documents processed: {len(all_docs)}")
    print(f"Saved to: {output_path}")
    print("\nNext step: python scripts/build_index.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
