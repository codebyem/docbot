import ollama
import json

EXTRACTION_PROMPT = """
Analysiere diese Konversation zwischen Patient und Zahnarztpraxis-Assistent.
Extrahiere folgende Informationen:

KONVERSATION:
{conversation}

Finde und extrahiere (falls vorhanden):
- patient_name: Vollständiger Name des Patienten
- patient_email: Email-Adresse
- patient_phone: Telefonnummer
- appointment_request: Gewünschter Termin oder Zeitraum
- reason: Grund des Besuchs (z.B. Zahnreinigung, Schmerzen, Kontrolle)
- notes: Andere wichtige Details

Antworte NUR mit einem JSON-Objekt in diesem Format:
{{
  "patient_name": "Name oder null",
  "patient_email": "email oder null",
  "patient_phone": "telefon oder null",
  "appointment_request": "terminwunsch oder null",
  "reason": "grund oder null",
  "notes": "notizen oder null"
}}

Wenn eine Information nicht in der Konversation vorhanden ist, nutze null.
"""


def extract_appointment_info(conversation_history):
    """
    Extrahiert strukturierte Daten aus der Konversation
    """
    # Konversation formatieren
    conversation_text = "\n".join([
        f"{'Patient' if msg['role'] == 'user' else 'Assistent'}: {msg['content']}"
        for msg in conversation_history
        if msg['role'] in ['user', 'model']
    ])

    prompt = EXTRACTION_PROMPT.format(conversation=conversation_text)

    try:
        response = ollama.generate(
            model="gemma3:4b",
            prompt=prompt,
            format="json"
        )

        # JSON parsen
        data = json.loads(response['response'])
        return data

    except Exception as e:
        print(f"FEHLER beim Extrahieren: {e}")
        # Fallback: Rohe Konversation als Notiz
        return {
            "patient_name": None,
            "patient_email": None,
            "patient_phone": None,
            "appointment_request": None,
            "reason": None,
            "notes": conversation_text[:500]
        }


# Test-Funktion
if __name__ == "__main__":
    # Test mit Beispiel-Konversation
    test_history = [
        {"role": "user", "content": "Hallo ich brauche einen Termin"},
        {"role": "model", "content": "Gerne! Wie ist Ihr Name?"},
        {"role": "user", "content": "Max Mustermann"},
        {"role": "model", "content": "Haben Sie eine Email oder Telefonnummer?"},
        {"role": "user", "content": "max@example.com"},
        {"role": "model", "content": "Wann hätten Sie Zeit?"},
        {"role": "user", "content": "Nächste Woche Dienstag"},
        {"role": "model", "content": "Worum geht es?"},
        {"role": "user", "content": "Zahnreinigung bitte"},
    ]

    print("Teste Daten-Extraktion...\n")
    info = extract_appointment_info(test_history)
    print(json.dumps(info, indent=2, ensure_ascii=False))