from __future__ import annotations

from dataclasses import dataclass

SAFE_RESPONSES = {
    "unclear": "Ich habe dich nicht gut verstanden. Kannst du das bitte kurz anders sagen?",
    "danger": "Dabei kann ich nicht helfen. Frag bitte sofort einen Erwachsenen.",
    "medical": "Dabei kann ich nicht sicher helfen. Hol bitte Mama, Papa oder eine andere erwachsene Person.",
    "violence": "Darüber reden wir lieber nicht. Magst du stattdessen etwas über Tiere hören?",
    "sexual": "Dazu kann ich nichts sagen. Bitte frag eine erwachsene Person, der du vertraust.",
    "personal_data": "Teile bitte keine privaten Daten. Frag lieber einen Erwachsenen.",
    "adult_help": "Hol bitte Mama oder Papa dazu.",
}


@dataclass(slots=True)
class SafetyService:
    def classify_input(self, text: str) -> str:
        lower = text.lower()
        if not lower.strip():
            return "unclear"
        if any(token in lower for token in ["adresse", "telefonnummer", "passwort"]):
            return "personal_data"
        if any(token in lower for token in ["weh", "krank", "fieber", "blutet"]):
            return "medical"
        if any(token in lower for token in ["messer", "bombe", "gift", "feuer machen"]):
            return "danger"
        if any(token in lower for token in ["hauen", "töten", "schießen"]):
            return "violence"
        if any(token in lower for token in ["sex", "nackt"]):
            return "sexual"
        if any(token in lower for token in ["mama", "papa", "hilfe"]):
            return "adult_help"
        return "ok"

    def safe_response(self, input_class: str) -> str:
        return SAFE_RESPONSES.get(input_class, "Ich kann dir gerade nur bei sicheren Themen helfen.")

    def check_output(self, text: str) -> str:
        trimmed = text.strip()
        if not trimmed:
            return "Magst du mir eine Frage stellen?"
        return trimmed
