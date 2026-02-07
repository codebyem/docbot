import os
import re
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from huggingface_hub import InferenceClient
from extract_info import extract_appointment_info
from email_sender import send_appointment_email

HF_MODEL = "meta-llama/Llama-3.2-3B-Instruct"

client = InferenceClient(api_key=os.getenv("HUGGINGFACE_API_KEY"))

SYSTEM_PROMPT = """
Du bist die virtuelle Assistenz der Zahnarztpraxis Dr. Müller in Lüneburg.

WICHTIG: Merke dir ALLE Informationen die der Patient bereits genannt hat.
Frage NIE zweimal nach der gleichen Information!

SAMMLE diese 4 Informationen:
1. Name des Patienten
2. Email ODER Telefonnummer
3. Terminwunsch (Tag/Uhrzeit)
4. Grund (z.B. Zahnreinigung, Schmerzen)

KONVERSATIONSFLUSS:
- Frage freundlich nach fehlenden Informationen
- Stelle MAXIMAL eine Frage pro Nachricht
- Wenn der Patient etwas bereits gesagt hat, frage NICHT nochmal danach
- Wenn du ALLE 4 Informationen hast, fasse kurz zusammen

WICHTIG:
- Wenn du die Zusammenfassung gibst, beende mit: "Soll ich diese Anfrage weiterleiten?"
- Wenn der Patient zustimmt (ja, gerne, ok, etc.), sage NUR: "ANFRAGE_SENDEN"

PRAXIS-INFOS:
- Öffnungszeiten: Mo-Fr 8-12 und 14-18 Uhr, Mi Nachmittag geschlossen
- Adresse: Musterstraße 123, 33602 Lüneburg
- Telefon: 0521-12345678

REGELN:
- Keine medizinischen Diagnosen
- Bei Notfällen → 112
- Freundlich & professionell

Antworte auf Deutsch.
"""

BLACKLIST_KEYWORDS = [
    'crack', 'kokain', 'droge', 'waffe', 'bombe',
    'mord', 'töten', 'selbstmord', 'terror',
    'hack', 'illegal', 'betrug'
]


def check_harmful_content(text):
    text_lower = text.lower()
    for keyword in BLACKLIST_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def check_if_complete(conversation_history):
    conv_text = " ".join([msg['content'] for msg in conversation_history if msg['role'] == 'user'])

    has_name = bool(re.search(r'\b[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+', conv_text))
    has_contact = bool(re.search(r'(@|\.de|\.com|\d{4,})', conv_text))
    has_time = bool(re.search(
        r'(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag|\d{1,2}:\d{2}|\d{1,2}\s?uhr|vormittag|nachmittag|morgen|heute)',
        conv_text.lower()))

    return has_name and has_contact and has_time


def chat_cloud(user_message, conversation_history=[], awaiting_confirmation=False):
    # Blacklist-Check
    if check_harmful_content(user_message):
        return (
            "Ich kann Ihnen bei dieser Anfrage nicht helfen. "
            "Bitte wenden Sie sich mit zahnmedizinischen Fragen an mich.",
            conversation_history,
            awaiting_confirmation
        )

    # Check ob User bestaetigt
    confirmation_words = ['ja', 'gerne', 'ok', 'klar', 'weiter', 'senden', 'schicken', 'yes']
    if awaiting_confirmation and any(word in user_message.lower() for word in confirmation_words):
        print("\n" + "=" * 60)
        print("EMAIL-VERSAND GESTARTET")
        print("=" * 60 + "\n")

        print("Schritt 1: Extrahiere Daten...")
        appointment_data = extract_appointment_info(conversation_history)

        print("Extrahierte Daten:")
        for key, value in appointment_data.items():
            print(f"   {key}: {value or 'nicht vorhanden'}")
        print()

        print("Schritt 2: Sende Email...")
        result = send_appointment_email(appointment_data, conversation_history)
        print()

        if result['success']:
            response = """
Perfekt! Ihre Terminanfrage wurde erfolgreich weitergeleitet.

Die Praxis wird sich in Kuerze bei Ihnen melden.

Gibt es noch etwas, bei dem ich Ihnen helfen kann?
            """.strip()

            print("=" * 60)
            print("EMAIL ERFOLGREICH VERSENDET!")
            print("=" * 60 + "\n")

            return response, [], False
        else:
            response = f"""
Entschuldigung, technisches Problem beim Versenden.

Bitte rufen Sie direkt an: 0521-12345678

Fehler: {result.get('error', 'Unbekannt')}
            """.strip()

            print("=" * 60)
            print("EMAIL-VERSAND FEHLGESCHLAGEN")
            print(f"Fehler: {result.get('error', 'Unbekannt')}")
            print("=" * 60 + "\n")

            return response, conversation_history, False

    # Normale Konversation via HuggingFace API
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in conversation_history:
        role = "assistant" if msg["role"] in ["model", "assistant"] else "user"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=HF_MODEL,
            messages=messages,
            max_tokens=512,
        )
        assistant_message = response.choices[0].message.content
    except Exception as e:
        print(f"FEHLER bei HuggingFace API: {e}")
        return (
            "Entschuldigung, es gibt gerade ein technisches Problem. "
            "Bitte versuchen Sie es erneut oder rufen Sie uns an: 0521-12345678",
            conversation_history,
            False
        )

    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": assistant_message})

    # Check ob wir jetzt genug Infos haben
    is_complete = check_if_complete(conversation_history)
    needs_confirmation = "weiterleiten" in assistant_message.lower() or "senden" in assistant_message.lower()

    if is_complete and needs_confirmation:
        return assistant_message, conversation_history, True

    return assistant_message, conversation_history, False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("HUGGINGFACE_API_KEY"):
        print("FEHLER: HUGGINGFACE_API_KEY nicht in .env gefunden!")
        print("Bitte eintragen: HUGGINGFACE_API_KEY=hf_...")
        exit(1)

    print("=" * 60)
    print("ZAHNARZTPRAXIS DR. MUELLER")
    print("   Virtueller Assistent (Cloud)")
    print("=" * 60)
    print(f"\nModel: {HF_MODEL}")
    print("Schreiben Sie 'exit' zum Beenden.\n")
    print("=" * 60 + "\n")

    history = []
    awaiting_confirm = False

    while True:
        user_input = input("Sie: ")

        if user_input.lower() in ['exit', 'quit', 'beenden']:
            print("\nAuf Wiedersehen!\n")
            break

        response, history, awaiting_confirm = chat_cloud(user_input, history, awaiting_confirm)
        print(f"\nAssistent: {response}\n")
