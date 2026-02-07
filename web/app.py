import streamlit as st
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from core.chatbot_cloud import chat_cloud

# ---------- Page Config ----------

st.set_page_config(
    page_title="Zahnarztpraxis Dr. Mueller",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------- Custom CSS ----------

st.markdown("""
<style>
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }

    /* Main Container */
    .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }

    /* Header */
    .header-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        text-align: center;
    }
    .header-card h1 {
        color: #333;
        font-size: 1.6rem;
        margin: 0 0 0.25rem 0;
    }
    .header-card p {
        color: #666;
        font-size: 0.95rem;
        margin: 0;
    }

    /* Chat Container */
    .chat-container {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        min-height: 400px;
        max-height: 600px;
        overflow-y: auto;
    }

    /* Chat Bubbles */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        margin-bottom: 0.5rem;
        padding: 0.5rem 0.75rem;
    }

    /* Input Styling */
    [data-testid="stChatInput"] textarea {
        border-radius: 24px !important;
        border: 2px solid #667eea !important;
        padding: 0.75rem 1.25rem !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #764ba2 !important;
        box-shadow: 0 0 0 2px rgba(118, 75, 162, 0.2) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9ff 0%, #eef0ff 100%);
    }
    [data-testid="stSidebar"] h1 {
        color: #667eea;
        font-size: 1.3rem;
    }
    [data-testid="stSidebar"] h3 {
        color: #444;
        font-size: 1rem;
        margin-top: 1.5rem;
    }

    .sidebar-info-box {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .sidebar-info-box p {
        margin: 0.25rem 0;
        font-size: 0.9rem;
        color: #333;
    }
    .sidebar-info-box .label {
        font-weight: 600;
        color: #667eea;
    }

    /* Reset Button */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 24px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.9;
        color: white;
        border: none;
    }

    /* Status Indicator */
    .status-online {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #4CAF50;
        border-radius: 50%;
        margin-right: 6px;
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .header-card {
            padding: 1rem;
        }
        .header-card h1 {
            font-size: 1.3rem;
        }
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------- Session State ----------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "awaiting_confirmation" not in st.session_state:
    st.session_state.awaiting_confirmation = False
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

WELCOME_MESSAGE = (
    "Willkommen in der Zahnarztpraxis Dr. Mueller! "
    "Ich bin Ihr virtueller Assistent und helfe Ihnen gerne bei der Terminvereinbarung.\n\n"
    "Nennen Sie mir einfach Ihren Namen, und wir legen los."
)

if not st.session_state.welcome_shown:
    st.session_state.messages.append({"role": "assistant", "content": WELCOME_MESSAGE})
    st.session_state.welcome_shown = True

# ---------- Sidebar ----------

with st.sidebar:
    st.markdown("# Zahnarztpraxis Dr. Mueller")

    st.markdown("### Praxis-Informationen")

    st.markdown("""
    <div class="sidebar-info-box">
        <p><span class="label">Adresse</span></p>
        <p>Musterstrasse 123<br>33602 Lueneburg</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-info-box">
        <p><span class="label">Oeffnungszeiten</span></p>
        <p>Mo - Fr: 8:00 - 12:00 Uhr</p>
        <p>Mo, Di, Do, Fr: 14:00 - 18:00 Uhr</p>
        <p>Mi Nachmittag: geschlossen</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-info-box">
        <p><span class="label">Kontakt</span></p>
        <p>Tel: 0521-12345678</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Haeufige Fragen")

    with st.expander("Welche Infos braucht der Bot?"):
        st.write(
            "1. Ihren vollstaendigen Namen\n"
            "2. Email oder Telefonnummer\n"
            "3. Ihren Terminwunsch (Tag/Uhrzeit)\n"
            "4. Grund des Besuchs"
        )

    with st.expander("Wie laeuft die Terminanfrage ab?"):
        st.write(
            "Der Assistent sammelt Ihre Daten und leitet die Anfrage "
            "per Email an die Praxis weiter. Das Praxis-Team meldet sich "
            "dann bei Ihnen zur Bestätigung."
        )

    with st.expander("Was bei Notfaellen?"):
        st.write("Bei zahnmedizinischen Notfaellen rufen Sie bitte **112** oder "
                 "die Praxis direkt an: **0521-12345678**")

    st.markdown("---")

    if st.button("Neue Konversation"):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
        st.session_state.conversation_history = []
        st.session_state.awaiting_confirmation = False
        st.rerun()

# ---------- Header ----------

st.markdown("""
<div class="header-card">
    <h1>Zahnarztpraxis Dr. Mueller</h1>
    <p><span class="status-online"></span>Virtueller Assistent - Online</p>
</div>
""", unsafe_allow_html=True)

# ---------- Chat Messages ----------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------- User Input ----------

if user_input := st.chat_input("Ihre Nachricht..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Einen Moment bitte..."):
            try:
                response, new_history, new_confirmation = chat_cloud(
                    user_input,
                    list(st.session_state.conversation_history),
                    st.session_state.awaiting_confirmation,
                )
            except Exception as e:
                response = (
                    "Entschuldigung, ein unerwarteter Fehler ist aufgetreten. "
                    "Bitte versuchen Sie es erneut oder rufen Sie uns an: 0521-12345678"
                )
                new_history = st.session_state.conversation_history
                new_confirmation = False

        st.write(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.conversation_history = new_history
    st.session_state.awaiting_confirmation = new_confirmation

    # Balloons bei erfolgreichem Email-Versand
    if "erfolgreich weitergeleitet" in response.lower():
        st.balloons()
