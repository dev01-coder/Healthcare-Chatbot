"""
Emergency Detection Module
Detects life-threatening situations and returns emergency resources.
"""

import re
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Emergency keyword patterns
EMERGENCY_PATTERNS = {
    "cardiac": [
        r"\b(heart attack|chest pain|chest pressure|myocardial|cardiac arrest|palpitation)\b",
        r"\b(pain in (left )?arm|jaw pain|radiating pain)\b",
    ],
    "stroke": [
        r"\b(stroke|brain attack|face drooping|arm weakness|slurred speech|sudden headache)\b",
        r"\b(can't speak|face numb|sudden confusion|vision loss)\b",
    ],
    "breathing": [
        r"\b(can't breathe|difficulty breathing|shortness of breath|choking|not breathing)\b",
        r"\b(throat closing|throat swelling|anaphylaxis)\b",
    ],
    "suicide": [
        r"\b(suicide|suicidal|want to die|kill myself|end my life|self harm|cut myself)\b",
        r"\b(no reason to live|better off dead|can't go on)\b",
    ],
    "overdose": [
        r"\b(overdose|took too many pills|swallowed too much|poisoning)\b",
    ],
    "unconscious": [
        r"\b(unconscious|not responding|won't wake|passed out|fainted|seizure|convulsion)\b",
    ],
    "severe_bleeding": [
        r"\b(severe bleeding|won't stop bleeding|bleeding heavily|blood everywhere)\b",
    ],
}

EMERGENCY_RESPONSES = {
    "cardiac": {
        "title": "Possible Cardiac Emergency",
        "message": "These symptoms may indicate a heart attack. This is a medical emergency.",
        "actions": [
            "Call your local emergency number IMMEDIATELY",
            "Sit or lie down, stay calm",
            "Chew aspirin (325mg) if available and not allergic",
            "Do NOT drive yourself",
            "Unlock the door for emergency services",
        ],
    },
    "stroke": {
        "title": "Possible Stroke Emergency",
        "message": "Remember FAST: Face drooping, Arm weakness, Speech difficulty = Time to call emergency. Every minute counts for stroke treatment.",
        "actions": [
            "Call your local emergency number IMMEDIATELY",
            "Note the exact time symptoms started",
            "Do NOT give food or water",
            "Keep the person calm and still",
            "Go to nearest emergency room immediately",
        ],
    },
    "breathing": {
        "title": "Breathing Emergency",
        "message": "Difficulty breathing is a medical emergency requiring immediate attention.",
        "actions": [
            "Call your local emergency number IMMEDIATELY",
            "Sit upright to help breathing",
            "If known asthmatic, use inhaler",
            "If allergic reaction: use EpiPen if available",
            "Loosen tight clothing",
        ],
    },
    "suicide": {
        "title": "You Are Not Alone",
        "message": "It sounds like you may be going through something very painful right now. Your life has value and help is available.",
        "actions": [
            "Call your local crisis helpline",
            "Reach out to a trusted friend or family member",
            "Go to the nearest hospital emergency room",
            "You deserve support — please reach out",
        ],
    },
    "overdose": {
        "title": "Overdose Emergency",
        "message": "A suspected overdose is a medical emergency requiring immediate treatment.",
        "actions": [
            "Call your local emergency number IMMEDIATELY",
            "Tell them what was taken and how much if known",
            "Keep the person awake and breathing",
            "Do NOT induce vomiting unless told to by medical staff",
            "Save any medication bottles to show responders",
        ],
    },
    "unconscious": {
        "title": "Emergency — Person Unresponsive",
        "message": "An unresponsive person requires immediate emergency medical care.",
        "actions": [
            "Call your local emergency number IMMEDIATELY",
            "Check for breathing",
            "If not breathing and you know CPR, begin compressions",
            "Place in recovery position if breathing",
            "Stay on line with emergency services",
        ],
    },
    "severe_bleeding": {
        "title": "Severe Bleeding Emergency",
        "message": "Severe uncontrolled bleeding is a life-threatening emergency.",
        "actions": [
            "Call your local emergency number IMMEDIATELY",
            "Apply firm, direct pressure to wound",
            "Use clean cloth or bandage",
            "Do NOT remove the cloth even if it soaks through — add more on top",
            "Keep the person lying down and warm",
        ],
    },
}


def detect_emergency(text: str) -> Optional[Dict]:
    """
    Check if the user message contains emergency keywords.
    Returns emergency response dict if detected, None otherwise.
    """
    text_lower = text.lower()

    for emergency_type, patterns in EMERGENCY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                logger.warning(
                    "Emergency detected: type=%s, input=%s",
                    emergency_type, text[:100],
                )
                return {
                    "is_emergency": True,
                    "type": emergency_type,
                    **EMERGENCY_RESPONSES[emergency_type],
                }

    return None


def get_disclaimer() -> str:
    """Return the standard medical disclaimer."""
    return (
        "\n\n---\n"
        "**Medical Disclaimer:** This information is for educational purposes only "
        "and does not constitute medical advice. Always consult a qualified healthcare "
        "professional for diagnosis and treatment. In case of emergency, call your local emergency number."
    )


def is_advice_query(query: str) -> bool:
    """Check if the query is asking for medical advice."""
    advice_keywords = [
        "should i", "what treatment", "how to treat", "recommend",
        "advice", "suggest", "what medicine", "what medication",
        "dosage", "dose", "can i take", "is it safe", "what do you think"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in advice_keywords)
