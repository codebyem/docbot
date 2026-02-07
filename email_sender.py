import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


def send_appointment_email(appointment_data, conversation_history):
    """
    Sendet Email via Gmail SMTP (kein SSL-Problem!)
    """

    sender_email = os.getenv('GMAIL_ADDRESS')
    sender_password = os.getenv('GMAIL_APP_PASSWORD')
    receiver_email = os.getenv('PRAXIS_EMAIL')

    # HTML Email (schön formatiert)
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                color: #333;
            }}
            .header {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                padding: 20px; 
                border-radius: 8px 8px 0 0;
            }}
            .content {{ 
                padding: 20px; 
                background: #ffffff;
            }}
            .info-box {{ 
                background: #f5f5f5; 
                padding: 15px; 
                margin: 10px 0; 
                border-left: 4px solid #667eea; 
                border-radius: 4px;
            }}
            .label {{ 
                font-weight: bold; 
                color: #667eea; 
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Neue Terminanfrage</h2>
            <p>Eingegangen am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}</p>
        </div>

        <div class="content">
            <h3>Patienteninformationen:</h3>
            <div class="info-box">
                <p><span class="label">Name:</span> {appointment_data.get('patient_name') or 'Nicht angegeben'}</p>
                <p><span class="label">Email:</span> {appointment_data.get('patient_email') or 'Nicht angegeben'}</p>
                <p><span class="label">Telefon:</span> {appointment_data.get('patient_phone') or 'Nicht angegeben'}</p>
            </div>

            <h3>Termindetails:</h3>
            <div class="info-box">
                <p><span class="label">Terminwunsch:</span> {appointment_data.get('appointment_request') or 'Nicht spezifiziert'}</p>
                <p><span class="label">Grund:</span> {appointment_data.get('reason') or 'Nicht angegeben'}</p>
            </div>

            {f'<h3>Zusätzliche Notizen:</h3><div class="info-box"><p>{appointment_data.get("notes")}</p></div>' if appointment_data.get('notes') else ''}

            <div class="footer">
                <p>Diese Anfrage wurde automatisch vom virtuellen Praxis-Assistenten erstellt.</p>
                <p>Bitte kontaktieren Sie den Patienten zeitnah.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Plain-Text Fallback
    text_content = f"""
NEUE TERMINANFRAGE - {datetime.now().strftime('%d.%m.%Y %H:%M Uhr')}

PATIENTENINFORMATIONEN:
Name: {appointment_data.get('patient_name') or 'Nicht angegeben'}
Email: {appointment_data.get('patient_email') or 'Nicht angegeben'}
Telefon: {appointment_data.get('patient_phone') or 'Nicht angegeben'}

TERMINDETAILS:
Terminwunsch: {appointment_data.get('appointment_request') or 'Nicht spezifiziert'}
Grund: {appointment_data.get('reason') or 'Nicht angegeben'}
Notizen: {appointment_data.get('notes') or 'Keine'}

---
Automatisch erstellt vom Praxis-Assistenten
Bitte kontaktieren Sie den Patienten zeitnah
    """

    # Email zusammenbauen
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Terminanfrage: {appointment_data.get('patient_name', 'Neuer Patient')}"
    message["From"] = f"Praxis-Assistent <{sender_email}>"
    message["To"] = receiver_email

    # Text und HTML anhängen
    part1 = MIMEText(text_content, "plain", "utf-8")
    part2 = MIMEText(html_content, "html", "utf-8")
    message.attach(part1)
    message.attach(part2)

    # Email senden
    try:
        print("Verbinde mit Gmail...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(0)

        print("Starte TLS...")
        server.starttls()

        print("Login...")
        server.login(sender_email, sender_password)

        print("Sende Email...")
        server.sendmail(sender_email, receiver_email, message.as_string())

        print("Verbindung geschlossen.")
        server.quit()

        print("Email erfolgreich versendet!")

        return {
            "success": True,
            "message": "Email erfolgreich versendet"
        }

    except smtplib.SMTPAuthenticationError:
        error_msg = "Gmail Login fehlgeschlagen. Checke GMAIL_ADDRESS und GMAIL_APP_PASSWORD in .env"
        print(f"FEHLER: {error_msg}")
        return {"success": False, "error": error_msg}

    except Exception as e:
        print(f"FEHLER beim Email-Versand: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Email konnte nicht versendet werden"
        }


# Test-Funktion
if __name__ == "__main__":
    print("=" * 60)
    print("TESTE GMAIL SMTP EMAIL-VERSAND")
    print("=" * 60 + "\n")

    # Checke ob .env richtig konfiguriert ist
    if not os.getenv('GMAIL_ADDRESS'):
        print("FEHLER: GMAIL_ADDRESS nicht in .env gefunden!")
        print("Bitte in .env eintragen: GMAIL_ADDRESS=deine-email@gmail.com")
        exit(1)

    if not os.getenv('GMAIL_APP_PASSWORD'):
        print("FEHLER: GMAIL_APP_PASSWORD nicht in .env gefunden!")
        print("Bitte in .env eintragen: GMAIL_APP_PASSWORD=dein-app-passwort")
        exit(1)

    print(f"Gmail Adresse: {os.getenv('GMAIL_ADDRESS')}")
    print(f"Ziel-Email: {os.getenv('PRAXIS_EMAIL')}")
    print()

    # Test-Daten
    test_data = {
        "patient_name": "Emma Test Schmidt",
        "patient_email": "emma.test@example.com",
        "patient_phone": "0521-123456",
        "appointment_request": "Dienstag 15:00 Uhr",
        "reason": "Zahnreinigung",
        "notes": "Dies ist eine Testmail vom DocBot System"
    }

    test_history = [
        {"role": "user", "content": "Hallo ich brauche einen Termin"},
        {"role": "model", "content": "Gerne! Wie ist Ihr Name?"},
        {"role": "user", "content": "Emma Test Schmidt"},
    ]

    print("Sende Test-Email...\n")
    result = send_appointment_email(test_data, test_history)

    print("\n" + "=" * 60)
    if result['success']:
        print("TEST ERFOLGREICH!")
        print("=" * 60)
        print("\nChecke dein Email-Postfach!")
        print(f"   Empfaenger: {os.getenv('PRAXIS_EMAIL')}")
        print("   Subject: Terminanfrage: Emma Test Schmidt")
        print("\n   (Auch Spam-Ordner checken!)\n")
    else:
        print("TEST FEHLGESCHLAGEN")
        print("=" * 60)
        print(f"\nFehler: {result.get('error', 'Unbekannt')}\n")
        print("Mögliche Ursachen:")
        print("1. Gmail App-Passwort falsch")
        print("2. 2-Step Verification nicht aktiviert")
        print("3. GMAIL_ADDRESS oder GMAIL_APP_PASSWORD falsch in .env")