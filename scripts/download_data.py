"""
Healthcare RAG Bot - Dataset Downloader
Downloads MedQuAD (47K medical Q&A pairs from NIH) + sample data.
Run: python scripts/download_data.py
"""

import os
import json
import csv
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_medquad():
    """Download MedQuAD dataset from HuggingFace."""
    dest = RAW_DIR / "medquad.csv"
    if dest.exists():
        print(f"\n  Already exists: medquad.csv — skipping")
        return True

    print("\n  Downloading: MedQuAD Medical Q&A Dataset")
    print("   Source: NIH (12 websites, 47K+ Q&A pairs)")
    print("   This may take 1-2 minutes on first run...")

    try:
        from datasets import load_dataset

        dataset = load_dataset("keivalya/MedQuad-MedicalQnADataset", split="train")
        print(f"   Loaded {len(dataset)} records from HuggingFace")

        # Save as CSV
        with open(dest, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["question", "answer", "focus_area"])
            writer.writeheader()
            for row in dataset:
                writer.writerow({
                    "question": row.get("Question", ""),
                    "answer": row.get("Answer", ""),
                    "focus_area": row.get("focus_area", "Disease"),
                })

        print(f"   Saved to {dest}")
        return True

    except Exception as e:
        print(f"   Failed to download MedQuAD: {e}")
        print("   Will use sample data only.")
        return False


def create_sample_data():
    """Create comprehensive sample healthcare data."""
    print("\n  Creating comprehensive sample healthcare dataset...")

    sample_qa = [
        {"question": "What is diabetes?", "answer": "Diabetes is a chronic condition where the body cannot properly regulate blood sugar (glucose) levels. Type 1 diabetes occurs when the immune system attacks insulin-producing cells. Type 2 diabetes occurs when the body becomes resistant to insulin or doesn't produce enough. Symptoms include frequent urination, excessive thirst, fatigue, and blurred vision. Always consult a doctor for proper diagnosis."},
        {"question": "What are symptoms of hypertension?", "answer": "Hypertension (high blood pressure) is often called the 'silent killer' because it usually has no obvious symptoms. When symptoms do occur, they may include headaches, shortness of breath, nosebleeds, flushing, dizziness, or chest pain. Blood pressure is measured in mmHg. Normal is below 120/80. Consult your doctor regularly for blood pressure checks."},
        {"question": "What is asthma?", "answer": "Asthma is a chronic lung disease that inflames and narrows the airways, causing recurring periods of wheezing, chest tightness, shortness of breath, and coughing. Triggers include allergens, exercise, cold air, and respiratory infections. Treatment involves inhalers (bronchodilators and corticosteroids). Seek immediate medical help if you have a severe asthma attack."},
        {"question": "What causes fever?", "answer": "Fever is a temporary rise in body temperature, usually due to illness. Common causes include bacterial infections (like pneumonia, UTI), viral infections (flu, COVID-19), heat exhaustion, certain medications, and inflammatory conditions. A fever above 103F (39.4C) or lasting more than 3 days requires medical attention. Stay hydrated and consult a doctor if concerned."},
        {"question": "What is a heart attack?", "answer": "A heart attack (myocardial infarction) occurs when blood flow to part of the heart is blocked. Symptoms include chest pain or pressure, pain spreading to arm/jaw/neck, shortness of breath, cold sweat, nausea. CALL EMERGENCY SERVICES IMMEDIATELY if you suspect a heart attack. Time is critical — the sooner treatment begins, the better the outcome."},
        {"question": "What is depression?", "answer": "Depression is a serious mental health condition characterized by persistent sadness, loss of interest, changes in sleep and appetite, difficulty concentrating, and feelings of worthlessness. It is treatable through therapy, medication, or a combination. If you're experiencing symptoms, please reach out to a mental health professional. If you're in crisis, contact a crisis helpline immediately."},
        {"question": "What are the side effects of ibuprofen?", "answer": "Ibuprofen (Advil, Motrin) is a nonsteroidal anti-inflammatory drug (NSAID). Common side effects include stomach upset, nausea, heartburn, and dizziness. Serious but rare side effects include stomach bleeding, kidney problems, and increased risk of heart attack or stroke. Do not exceed recommended doses. Take with food to reduce stomach upset. Avoid if you have kidney disease or stomach ulcers. Always follow your doctor's instructions."},
        {"question": "How do I know if I have COVID-19?", "answer": "COVID-19 symptoms include fever, cough, shortness of breath, fatigue, body aches, headache, loss of taste or smell, sore throat, and runny nose. Symptoms appear 2-14 days after exposure. Severity ranges from mild to critical. Get tested if you have symptoms. Seek emergency care if you have trouble breathing, persistent chest pain, confusion, or bluish lips. Follow current health authority guidelines in your area."},
        {"question": "What is anemia?", "answer": "Anemia is a condition where you don't have enough healthy red blood cells to carry adequate oxygen to body tissues. Symptoms include fatigue, weakness, pale skin, shortness of breath, dizziness, and cold hands and feet. Causes include iron deficiency (most common), vitamin B12 deficiency, chronic disease, and blood loss. Treatment depends on the cause. A blood test can diagnose anemia — consult your doctor."},
        {"question": "What is the difference between bacteria and viruses?", "answer": "Bacteria are single-celled living organisms that can reproduce independently. They can be treated with antibiotics. Examples of bacterial infections: strep throat, UTI, tuberculosis. Viruses are much smaller and need a host cell to reproduce. They cannot be treated with antibiotics. Antivirals exist for some viruses. Examples: flu, COVID-19, HIV. Using antibiotics for viral infections is ineffective and contributes to antibiotic resistance."},
        {"question": "What is cholesterol?", "answer": "Cholesterol is a waxy substance found in your blood. Your body needs it to build cells, but too much can increase risk of heart disease. LDL ('bad') cholesterol builds up in arteries. HDL ('good') cholesterol removes LDL from arteries. High cholesterol usually has no symptoms. It's detected through a blood test. Management includes diet changes, exercise, and sometimes medication (statins). Get your cholesterol checked regularly."},
        {"question": "What is appendicitis?", "answer": "Appendicitis is inflammation of the appendix, a small organ in the lower right abdomen. Symptoms include sudden pain beginning around the navel then shifting to lower right abdomen, nausea, vomiting, fever, and loss of appetite. The pain usually worsens with movement. APPENDICITIS IS A MEDICAL EMERGENCY. Go to the emergency room immediately. Untreated appendicitis can rupture and cause life-threatening infection."},
        {"question": "How much water should I drink daily?", "answer": "General guidelines suggest about 8 cups (2 liters) of water per day for adults, but needs vary. The National Academies recommend 3.7 liters (men) and 2.7 liters (women) total daily water from all beverages and food. Factors affecting needs include climate, physical activity, body size, and health conditions. Signs of dehydration: dark urine, dry mouth, fatigue, dizziness. Consult your doctor if you have kidney or heart conditions that affect fluid intake."},
        {"question": "What is pneumonia?", "answer": "Pneumonia is an infection that inflames the air sacs in one or both lungs. Symptoms include cough with phlegm, fever, chills, and difficulty breathing. It can be caused by bacteria, viruses, or fungi. Bacterial pneumonia is treated with antibiotics. Viral pneumonia includes COVID-19 pneumonia. High-risk groups: elderly, young children, and immunocompromised individuals. Seek medical care if you suspect pneumonia — it can be serious."},
        {"question": "What is BMI?", "answer": "BMI (Body Mass Index) is a measure of body fat based on height and weight. BMI = weight(kg) / height(m)^2. Categories: Underweight: <18.5, Normal: 18.5-24.9, Overweight: 25-29.9, Obese: 30+. BMI is a screening tool, not a diagnostic measure. It doesn't distinguish between muscle and fat, and doesn't account for age, sex, or ethnicity differences. Consult your healthcare provider for a complete health assessment."},
        {"question": "What is a stroke?", "answer": "A stroke occurs when blood supply to part of the brain is cut off. Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call emergency services. Other symptoms: sudden numbness, confusion, vision problems, severe headache. STROKE IS A MEDICAL EMERGENCY. Call emergency services immediately. Every minute counts — the faster treatment begins, the better the chance of recovery. Do not drive yourself; call an ambulance."},
        {"question": "What are common allergies?", "answer": "Allergies occur when your immune system reacts to a harmless substance (allergen). Common types: seasonal allergies (pollen — sneezing, itchy eyes), food allergies (nuts, shellfish — hives, swelling), drug allergies (rashes, anaphylaxis), pet allergies (dander — congestion, sneezing). Treatment includes antihistamines, nasal sprays, and avoiding triggers. Severe allergic reactions (anaphylaxis) require immediate emergency care with an EpiPen."},
        {"question": "What is thyroid disease?", "answer": "The thyroid gland regulates metabolism. Hypothyroidism (underactive): fatigue, weight gain, cold sensitivity, constipation, dry skin. Hyperthyroidism (overactive): weight loss, rapid heartbeat, anxiety, tremors, heat sensitivity. Both are diagnosed with blood tests (TSH, T3, T4). Hypothyroidism is treated with levothyroxine. Hyperthyroidism may be treated with medication, radioactive iodine, or surgery. Consult an endocrinologist for proper management."},
        {"question": "What are kidney stones?", "answer": "Kidney stones are hard deposits of minerals and salts that form inside your kidneys. Symptoms include severe flank pain, blood in urine, nausea, vomiting, and frequent urination. Pain is often described as the worst pain imaginable. Small stones may pass naturally with lots of water and pain medication. Large stones may require lithotripsy (shock wave therapy) or surgery. Prevention: drink plenty of water, reduce sodium and animal protein intake."},
        {"question": "What is gastroesophageal reflux disease (GERD)?", "answer": "GERD is a chronic digestive condition where stomach acid frequently flows back into the esophagus, causing heartburn and irritation. Symptoms: burning sensation in chest (heartburn), regurgitation of food or sour liquid, difficulty swallowing, chronic cough. Lifestyle changes help: avoid spicy/fatty foods, don't lie down after eating, elevate head during sleep. Medications include antacids, H2 blockers, and proton pump inhibitors (PPIs). See a doctor if symptoms persist."},
        {"question": "What are UTIs (urinary tract infections)?", "answer": "UTIs are infections in any part of the urinary system (kidneys, bladder, urethra). Women are more susceptible. Symptoms: frequent urination, burning sensation during urination, cloudy or strong-smelling urine, pelvic pain. Most UTIs are caused by bacteria and treated with antibiotics. Drink plenty of water to help flush bacteria. See a doctor promptly — untreated UTIs can spread to the kidneys and become serious."},
        {"question": "What is the flu (influenza)?", "answer": "Influenza is a viral respiratory infection. Symptoms: sudden fever, body aches, fatigue, cough, sore throat, headache. Unlike a common cold, flu comes on suddenly and can be severe. Complications include pneumonia, especially in elderly and immunocompromised. Treatment: rest, fluids, antiviral medication (oseltamivir) if caught early. Annual flu vaccination is the best prevention. Seek emergency care if you have difficulty breathing or persistent chest pain."},
        {"question": "What are common skin conditions?", "answer": "Common skin conditions include: eczema (dry, itchy patches), psoriasis (scaly patches), acne (pimples, blackheads), fungal infections (ringworm, athlete's foot), contact dermatitis (red rash from irritants). Most are treatable with topical creams, lifestyle changes, or medication. See a dermatologist for persistent or severe skin issues. In humid weather, fungal infections are more common — keep skin dry and clean."},
        {"question": "What is obesity and its risks?", "answer": "Obesity is having excess body fat (BMI 30+). Health risks: type 2 diabetes, heart disease, stroke, certain cancers, sleep apnea, joint problems, fatty liver disease. Management includes dietary changes, regular exercise, behavioral therapy, and sometimes medication or surgery. Even 5-10% weight loss can significantly improve health. Consult a doctor for a personalized weight management plan. Fad diets are not recommended — focus on sustainable lifestyle changes."},
        {"question": "What are childhood vaccines?", "answer": "Recommended childhood vaccines: BCG (tuberculosis) at birth, Polio drops at birth and multiple doses, DPT-HepB-Hib at 6, 10, 14 weeks, Measles at 9 and 15 months, Pentavalent vaccine. Additional recommended: Hepatitis A, Typhoid, Rotavirus, Pneumococcal. Keep your child's vaccination card updated. Visit your healthcare provider for vaccination. Vaccines are safe and the best protection against deadly diseases."},
        {"question": "How to manage diabetes naturally?", "answer": "While diabetes requires medical management, lifestyle changes help: 1) Eat a balanced diet low in refined carbs and sugar. 2) Exercise 30 minutes daily (walking is excellent). 3) Maintain healthy weight. 4) Monitor blood sugar regularly. 5) Take medications as prescribed. 6) Manage stress. 7) Get adequate sleep. Never stop prescribed medications without consulting your doctor. Natural remedies complement but do NOT replace medical treatment. Regular HbA1c tests are important."},
        {"question": "What is dengue fever?", "answer": "Dengue is a mosquito-borne viral infection common in tropical and subtropical regions. Symptoms: high fever (104F), severe headache, pain behind eyes, joint and muscle pain, skin rash. Severe dengue (dengue hemorrhagic fever) causes bleeding, blood plasma leakage, and organ impairment — this is life-threatening. Prevention: eliminate standing water, use mosquito repellent, wear long sleeves. There is no specific treatment — use paracetamol (NOT aspirin/ibuprofen). Seek immediate medical care if symptoms worsen."},
        {"question": "What is typhoid fever?", "answer": "Typhoid fever is a bacterial infection (Salmonella typhi) spread through contaminated food and water. Symptoms: sustained high fever (103-104F), weakness, stomach pain, headache, loss of appetite. Diagnosis: Widal test or blood culture. Treatment: antibiotics (ciprofloxacin, azithromycin) — complete the full course. Prevention: drink clean/boiled water, eat freshly cooked food, wash hands frequently. Complications include intestinal bleeding and perforation if untreated."},
        {"question": "What is hepatitis?", "answer": "Hepatitis is liver inflammation. Types: Hep A (fecal-oral, contaminated food/water — acute, resolves on its own), Hep B (blood/sexual contact — can become chronic), Hep C (blood contact — often chronic, leading to cirrhosis). Symptoms: jaundice (yellow skin/eyes), fatigue, abdominal pain, dark urine, nausea. Hep B vaccine is available. Hep C is treatable with antivirals. Get tested regularly if at risk."},
        {"question": "How to prevent heart disease?", "answer": "Heart disease prevention: 1) Don't smoke (biggest modifiable risk factor). 2) Exercise 150 minutes/week moderate activity. 3) Eat heart-healthy diet (fruits, vegetables, whole grains, fish). 4) Control blood pressure (<120/80 mmHg). 5) Manage cholesterol. 6) Maintain healthy weight. 7) Control diabetes. 8) Limit alcohol. 9) Manage stress. 10) Get regular checkups. Family history increases risk — be extra vigilant if parents had heart disease before age 55 (men) or 65 (women)."},
        {"question": "What are the warning signs of cancer?", "answer": "Common cancer warning signs: unexplained weight loss, persistent fatigue, unusual bleeding or discharge, thickening lump in breast/testicle, indigestion or difficulty swallowing, persistent cough or hoarseness, changes in bowel/bladder habits, non-healing sores, fever, night sweats. Early detection dramatically improves outcomes. Regular screenings: mammograms (breast), Pap smears (cervical), colonoscopy (colorectal), skin checks. Breast cancer is the most common cancer in women worldwide — regular self-examination is important."},
        {"question": "What is mental health?", "answer": "Mental health encompasses emotional, psychological, and social well-being. It affects how we think, feel, and act. Common conditions: depression (persistent sadness), anxiety (excessive worry), PTSD (trauma-related), bipolar disorder (mood swings). Treatment options: psychotherapy (talk therapy), medication, lifestyle changes, support groups. Mental health is just as important as physical health. Stigma prevents many from seeking help — remember that seeking help is a sign of strength, not weakness."},
        {"question": "How to improve sleep quality?", "answer": "Good sleep hygiene tips: 1) Maintain consistent sleep schedule (same time daily). 2) Create dark, quiet, cool sleeping environment. 3) Avoid screens 1 hour before bed. 4) Limit caffeine after 2 PM. 5) Avoid heavy meals before sleep. 6) Exercise regularly but not close to bedtime. 7) Manage stress with relaxation techniques. 8) Avoid naps after 3 PM. Adults need 7-9 hours. Chronic insomnia may indicate underlying conditions — consult a doctor. Sleep apnea (loud snoring, breathing pauses) requires medical treatment."},
        {"question": "What are STIs (sexually transmitted infections)?", "answer": "STIs are infections spread through sexual contact. Common types: chlamydia, gonorrhea, syphilis, herpes, HPV, HIV. Symptoms: unusual discharge, sores/bumps, burning during urination, pain during sex. Many STIs can be asymptomatic. Prevention: use condoms, limit partners, get tested regularly. Treatment: bacterial STIs treated with antibiotics; viral STIs managed with antivirals. Untreated STIs can cause infertility, chronic pain, and increase HIV risk. Get tested at any clinic — testing is confidential."},
        {"question": "How to manage chronic pain?", "answer": "Chronic pain (lasting >3 months) requires a multimodal approach: 1) Medications: NSAIDs, acetaminophen, nerve pain medications (gabapentin). 2) Physical therapy. 3) Exercise (swimming, walking, yoga). 4) Cognitive behavioral therapy (CBT). 5) Sleep hygiene. 6) Stress management. 7) Alternative therapies: acupuncture, massage. Avoid long-term opioid use unless absolutely necessary. Work with your doctor to find the right combination. Pain management is a journey — be patient with the process."},
    ]

    sample_path = RAW_DIR / "sample_qa.json"
    with open(sample_path, "w") as f:
        json.dump(sample_qa, f, indent=2)

    print(f"   Created {len(sample_qa)} sample Q&A pairs at {sample_path}")
    return sample_path


def main():
    print("=" * 60)
    print("  Healthcare RAG Bot - Dataset Downloader")
    print("=" * 60)

    # Download MedQuAD (main dataset)
    medquad_ok = download_medquad()

    # Always create sample data as baseline
    create_sample_data()

    print("\n" + "=" * 60)
    if medquad_ok:
        print("  MedQuAD dataset ready (47K+ medical Q&A pairs)")
    else:
        print("  Using sample data only (MedQuAD download failed)")
    print("\n  Next step: Run python scripts/process_data.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
