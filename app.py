"""
Patient Appointment Tracker - Streamlit MVP (All-in-One)
Complete application with authentication, role-based dashboards, and CRUD operations
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import hashlib
import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai
from openai import OpenAI

# ============ FILE CONSTANTS ============
USERS_FILE = "users.json"
APPOINTMENTS_FILE = "appointments.json"
SCHEDULES_FILE = "schedules.json"
CHAT_LOGS_FILE = "chat_logs.json"

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PRIMARY_COLOR = "#0f4c75"
SECONDARY_COLOR = "#1f6f8b"
BACKGROUND_COLOR = "#f7f9fb"
CARD_COLOR = "#ffffff"
TEXT_COLOR = "#0f172a"
MUTED_COLOR = "#52606d"


def inject_global_styles():
    st.markdown(
        f"""
        <style>
        html, body, [data-testid="stAppViewContainer"] {{background: {BACKGROUND_COLOR}; color: {TEXT_COLOR};}}
        [data-testid="stSidebar"] {{background: linear-gradient(180deg, {PRIMARY_COLOR}, {SECONDARY_COLOR}) !important; color: #ffffff;}}
        [data-testid="stSidebar"] .css-1d391kg {{background: transparent !important; box-shadow:none !important;}}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{color: #f5f9ff !important;}}
        .section-header {{padding: 24px; border-radius: 24px; background: linear-gradient(135deg, {PRIMARY_COLOR}, {SECONDARY_COLOR}); color: white; margin-bottom: 18px;}}
        .section-header h1 {{margin: 0; font-size: 2rem;}}
        .section-header p {{margin: 8px 0 0; color: rgba(255,255,255,0.87); font-size: 1rem;}}
        .section-card {{background: {CARD_COLOR}; border-radius: 24px; padding: 24px; box-shadow: 0 18px 45px rgba(15, 20, 42, 0.08); margin-bottom: 22px;}}
        .stButton>button {{border-radius: 999px !important;}}
        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div>div, .stDateInput>div>div>input, .stTimeInput>div>div>input, .stNumberInput>div>div>input {{border-radius: 14px !important; border: 1px solid #dbe4ee !important; background: #f8fafc !important;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============ AUTHENTICATION FUNCTIONS ============

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users() -> dict:
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {"users": []}


def save_users(users_data: dict) -> None:
    """Save users to JSON file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=2)


def user_exists(email: str) -> bool:
    """Check if a user already exists"""
    users_data = load_users()
    return any(user["email"] == email for user in users_data["users"])


def register_user(email: str, password: str, full_name: str, role: str) -> dict:
    """
    Register a new user
    
    Args:
        email: User email
        password: User password
        full_name: User's full name
        role: "doctor" or "patient"
    
    Returns:
        dict with success status and message
    """
    if user_exists(email):
        return {"success": False, "message": "Email already registered"}
    
    if role not in ["doctor", "patient"]:
        return {"success": False, "message": "Invalid role"}
    
    users_data = load_users()
    new_user = {
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    
    users_data["users"].append(new_user)
    save_users(users_data)
    
    return {"success": True, "message": "Registration successful! Please log in."}


def login_user(email: str, password: str) -> dict:
    """
    Authenticate a user
    
    Args:
        email: User email
        password: User password
    
    Returns:
        dict with success status, user data if successful
    """
    users_data = load_users()
    password_hash = hash_password(password)
    
    for user in users_data["users"]:
        if user["email"] == email and user["password_hash"] == password_hash:
            return {
                "success": True,
                "user": {
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "role": user["role"]
                }
            }
    
    return {"success": False, "message": "Invalid email or password"}


# ============ DATA MANAGEMENT FUNCTIONS ============

def load_appointments() -> dict:
    """Load appointments from JSON file"""
    if os.path.exists(APPOINTMENTS_FILE):
        with open(APPOINTMENTS_FILE, "r") as f:
            return json.load(f)
    return {"appointments": []}


def save_appointments(data: dict) -> None:
    """Save appointments to JSON file"""
    with open(APPOINTMENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_schedules() -> dict:
    """Load doctor schedules from JSON file"""
    if os.path.exists(SCHEDULES_FILE):
        with open(SCHEDULES_FILE, "r") as f:
            return json.load(f)
    return {"schedules": []}


def save_schedules(data: dict) -> None:
    """Save doctor schedules to JSON file"""
    with open(SCHEDULES_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ============ AI CHATBOT SUPPORT ============

def is_openai_configured() -> bool:
    return bool(OPENAI_API_KEY and OPENAI_API_KEY.strip())


class AppointmentDataStore:
    def __init__(self, patient_email: str):
        self.patient_email = patient_email

    def get_context(self) -> str:
        appointments = get_patient_appointments(self.patient_email)
        schedules = load_schedules()
        context = {
            "patient_email": self.patient_email,
            "appointments": appointments,
            "available_schedules": [
                s for s in schedules["schedules"] if s["status"] == "available"
            ],
            "clinic_info": {
                "name": "Patient Appointment Tracker Clinic",
                "hours": "Monday to Friday, 9:00 AM to 5:00 PM",
                "policies": [
                    "Bring a valid ID and insurance card",
                    "Arrive 10 minutes early",
                    "Contact staff if you need to reschedule"
                ]
            }
        }
        return json.dumps(context, indent=2)


class ChatLoggerStore:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)

    def load_logs(self) -> list:
        if self.filepath.exists():
            with open(self.filepath, "r") as f:
                return json.load(f)
        return []

    def save_logs(self, logs: list) -> None:
        with open(self.filepath, "w") as f:
            json.dump(logs, f, indent=2)


class ClinicAssistantBot:
    def __init__(self, api_key: str, context_data: str):
        self.client = OpenAI(api_key=api_key)
        self.context_data = context_data

    def build_ai_prompt(self) -> str:
        return (
            "You are a helpful clinic assistant. Answer user questions based ONLY on the appointment "
            "data and clinic information provided below. Do not invent information. If the answer is not "
            "contained in the provided data, respond with a helpful message that you do not have enough "
            "information and suggest the user contact clinic staff.\n\n"
            "CLINIC CONTEXT:\n"
            f"{self.context_data}"
        )

    def get_ai_response(self, chat_history: list) -> str:
        system_message = {"role": "system", "content": self.build_ai_prompt()}
        messages = [system_message] + chat_history
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,
                max_tokens=300
            )
            return response.choices[0].message["content"].strip()
        except openai.RateLimitError:
            return (
                "Sorry, the AI request could not be completed because your OpenAI quota has been exceeded. "
                "Please check your OpenAI plan and billing details, or use a different API key."
            )
        except openai.OpenAIError:
            return (
                "Sorry, the AI service returned an error. Please check your API key, quota, and network connection. "
                "If the problem persists, review your OpenAI account settings."
            )


def get_ai_assistant_response(user_input: str, user_email: str, chat_history: list) -> str:
    if not is_openai_configured():
        return (
            "OPENAI_API_KEY was not found. Please add your OpenAI API key to the .env file and restart the app. "
            "The key should be set as OPENAI_API_KEY=\"your-actual-api-key-here\"."
        )

    context_data = AppointmentDataStore(user_email).get_context()
    bot = ClinicAssistantBot(api_key=OPENAI_API_KEY, context_data=context_data)
    return bot.get_ai_response(chat_history)

# ========== SCHEDULE MANAGEMENT (Doctor/Admin CRUD) ==========

def create_time_slot(doctor_email: str, date: str, time: str, duration_minutes: int = 30) -> dict:
    """Create an available time slot for a doctor"""
    schedules = load_schedules()
    slot_id = f"{doctor_email}_{date}_{time}".replace(" ", "_").replace(":", "-")

    if any(s["slot_id"] == slot_id for s in schedules["schedules"]):
        return {"success": False, "message": "A time slot at this date and time already exists."}
    
    new_slot = {
        "slot_id": slot_id,
        "doctor_email": doctor_email,
        "date": date,
        "time": time,
        "duration_minutes": duration_minutes,
        "status": "available",
        "created_at": datetime.now().isoformat()
    }
    
    schedules["schedules"].append(new_slot)
    save_schedules(schedules)
    
    return {"success": True, "message": "Time slot created", "slot_id": slot_id}


def get_doctor_schedule(doctor_email: str) -> List[Dict]:
    """Get all time slots for a specific doctor"""
    schedules = load_schedules()
    return [s for s in schedules["schedules"] if s["doctor_email"] == doctor_email]


def get_available_slots(doctor_email: str) -> List[Dict]:
    """Get only available time slots for a doctor"""
    schedules = load_schedules()
    return [s for s in schedules["schedules"] 
            if s["doctor_email"] == doctor_email and s["status"] == "available"]


def delete_time_slot(slot_id: str) -> dict:
    """Delete a time slot"""
    schedules = load_schedules()
    schedules["schedules"] = [s for s in schedules["schedules"] if s["slot_id"] != slot_id]
    save_schedules(schedules)
    return {"success": True, "message": "Time slot deleted"}


# ========== APPOINTMENT MANAGEMENT (Both Roles CRUD) ==========

def book_appointment(patient_email: str, patient_name: str, slot_id: str) -> dict:
    """Book an appointment for a patient"""
    schedules = load_schedules()
    
    slot = next((s for s in schedules["schedules"] if s["slot_id"] == slot_id), None)
    if not slot or slot["status"] != "available":
        return {"success": False, "message": "Time slot not available"}
    
    appointments = load_appointments()
    appointment_id = f"APT_{len(appointments['appointments']) + 1}_{datetime.now().timestamp()}"
    
    new_appointment = {
        "appointment_id": appointment_id,
        "patient_email": patient_email,
        "patient_name": patient_name,
        "doctor_email": slot["doctor_email"],
        "date": slot["date"],
        "time": slot["time"],
        "duration_minutes": slot["duration_minutes"],
        "status": "booked",
        "notes": "",
        "booked_at": datetime.now().isoformat()
    }
    
    appointments["appointments"].append(new_appointment)
    save_appointments(appointments)
    
    slot["status"] = "booked"
    save_schedules(schedules)
    
    return {"success": True, "message": "Appointment booked successfully", 
            "appointment_id": appointment_id}


def get_patient_appointments(patient_email: str) -> List[Dict]:
    """Get all appointments for a specific patient"""
    appointments = load_appointments()
    return [a for a in appointments["appointments"] if a["patient_email"] == patient_email]


def get_doctor_appointments(doctor_email: str) -> List[Dict]:
    """Get all appointments for a specific doctor's daily roster"""
    appointments = load_appointments()
    return [a for a in appointments["appointments"] if a["doctor_email"] == doctor_email]


def cancel_appointment(appointment_id: str) -> dict:
    """Cancel an appointment and free up the slot"""
    appointments = load_appointments()
    schedules = load_schedules()
    
    appointment = next((a for a in appointments["appointments"] 
                       if a["appointment_id"] == appointment_id), None)
    
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    appointment["status"] = "cancelled"
    save_appointments(appointments)
    
    slot_id = f"{appointment['doctor_email']}_{appointment['date']}_{appointment['time']}".replace(" ", "_").replace(":", "-")
    for slot in schedules["schedules"]:
        if slot["slot_id"] == slot_id:
            slot["status"] = "available"
    
    save_schedules(schedules)
    
    return {"success": True, "message": "Appointment cancelled"}


def reschedule_appointment(appointment_id: str, new_slot_id: str) -> dict:
    """Reschedule an appointment to a new time slot"""
    appointments = load_appointments()
    schedules = load_schedules()
    
    appointment = next((a for a in appointments["appointments"] 
                       if a["appointment_id"] == appointment_id), None)
    
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    new_slot = next((s for s in schedules["schedules"] if s["slot_id"] == new_slot_id), None)
    
    if not new_slot or new_slot["status"] != "available":
        return {"success": False, "message": "New time slot not available"}
    
    old_slot_id = f"{appointment['doctor_email']}_{appointment['date']}_{appointment['time']}".replace(" ", "_").replace(":", "-")
    for slot in schedules["schedules"]:
        if slot["slot_id"] == old_slot_id:
            slot["status"] = "available"
    
    appointment["date"] = new_slot["date"]
    appointment["time"] = new_slot["time"]
    appointment["duration_minutes"] = new_slot["duration_minutes"]
    
    new_slot["status"] = "booked"
    
    save_appointments(appointments)
    save_schedules(schedules)
    
    return {"success": True, "message": "Appointment rescheduled successfully"}


def update_appointment_status(appointment_id: str, new_status: str) -> dict:
    """Update appointment status (e.g., Completed, No-Show)"""
    appointments = load_appointments()
    
    appointment = next((a for a in appointments["appointments"] 
                       if a["appointment_id"] == appointment_id), None)
    
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    appointment["status"] = new_status
    save_appointments(appointments)
    
    return {"success": True, "message": f"Appointment status updated to {new_status}"}


def update_appointment_notes(appointment_id: str, notes: str) -> dict:
    """Update appointment notes"""
    appointments = load_appointments()
    
    appointment = next((a for a in appointments["appointments"] 
                       if a["appointment_id"] == appointment_id), None)
    
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    appointment["notes"] = notes
    save_appointments(appointments)
    
    return {"success": True, "message": "Notes updated"}


def get_week_dates(reference_date=None) -> list:
    """Return a list of 7 sequential dates starting from the Monday of the reference week."""
    current_date = reference_date if reference_date else datetime.now().date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    return [start_of_week + timedelta(days=i) for i in range(7)]


def get_slots_by_day(slots: List[Dict]) -> Dict[str, List[Dict]]:
    """Group slots by their date string."""
    grouped = {}
    for slot in slots:
        grouped.setdefault(slot["date"], []).append(slot)
    return grouped


def create_recurring_slots(doctor_email: str, start_date, end_date, weekdays: List[int], time: str, duration_minutes: int, frequency_weeks: int = 1) -> dict:
    """Create recurring time slots over a date range."""
    if not weekdays:
        return {"success": False, "message": "Please select at least one weekday."}

    current_date = start_date
    created = 0
    while current_date <= end_date:
        week_number = ((current_date - start_date).days // 7)
        if week_number % frequency_weeks == 0 and current_date.weekday() in weekdays:
            result = create_time_slot(doctor_email, current_date.strftime("%Y-%m-%d"), time, duration_minutes)
            if result["success"]:
                created += 1
        current_date += timedelta(days=1)

    if created == 0:
        return {"success": False, "message": "No recurring slots were created. Check your date range or weekday selection."}

    return {"success": True, "message": f"Created {created} recurring slot{'s' if created != 1 else ''}."}


# ============ CHATBOT FUNCTION ============

def get_chatbot_response(user_query: str, user_email: str, user_name: str) -> str:
    """Get a hardcoded response from the chatbot based on user query (Phase 1: 5 responses)"""
    query = user_query.lower().strip()
    
    # Response 1: When is my next appointment?
    if any(keyword in query for keyword in ["next appointment", "when is my appointment", 
                                              "schedule", "my appointment", "upcoming"]):
        appointments = get_patient_appointments(user_email)
        upcoming = [a for a in appointments if a["status"] in ["booked"]]
        
        if upcoming:
            apt = upcoming[0]
            return f"Your next appointment is scheduled for {apt['date']} at {apt['time']} with Dr. {apt['doctor_email']}. Duration: {apt['duration_minutes']} minutes."
        else:
            return f"You don't have any upcoming appointments scheduled. Please book one through your dashboard!"
    
    # Response 2: How do I cancel my appointment?
    elif any(keyword in query for keyword in ["cancel", "how to cancel", "remove appointment", 
                                                "delete appointment"]):
        return "To cancel your appointment, go to your Dashboard, find your booked appointment in the 'My Appointments' section, and click the 'Cancel' button. Your time slot will be freed up and available for other patients."
    
    # Response 3: What are the clinic hours?
    elif any(keyword in query for keyword in ["hours", "clinic hours", "when open", "available hours", 
                                                "operating hours"]):
        return "Our clinic operates Monday through Friday, 9:00 AM to 5:00 PM. We are closed on weekends and public holidays. Please book your appointment within these hours."
    
    # Response 4: How do I reschedule?
    elif any(keyword in query for keyword in ["reschedule", "change appointment", "move appointment", 
                                                "different time", "reschedule appointment"]):
        return "To reschedule your appointment, go to your Dashboard, select the appointment you want to change, and click 'Reschedule'. Choose from the available time slots and confirm your new appointment time."
    
    # Response 5: What do I need to bring?
    elif any(keyword in query for keyword in ["bring", "prepare", "what to bring", "documents", 
                                                "insurance", "id required"]):
        return "Please bring your valid ID and insurance card to your appointment. Also, bring any relevant medical records or previous test results if available. Arrive 10 minutes early to check in."
    
    # Default response
    else:
        return f"Hi {user_name}! I'm the clinic's AI assistant. I can help you with questions about:\n" \
               "1. When is my next appointment?\n" \
               "2. How do I cancel my appointment?\n" \
               "3. What are the clinic hours?\n" \
               "4. How do I reschedule?\n" \
               "5. What do I need to bring?\n\n" \
               "Please ask me any of these questions, or contact our staff directly for more information!"


# ============ PAGE CONFIG AND INITIALIZATION ============

st.set_page_config(page_title="Patient Appointment Tracker", layout="wide", page_icon="🏥")
inject_global_styles()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "login"


# ============ SIDEBAR NAVIGATION ============

def sidebar_navigation():
    """Render sidebar with navigation and logout"""
    with st.sidebar:
        st.markdown(
            """
            <div style='padding: 18px 0 12px;'>
                <h2 style='margin:0;color:#ffffff;'>🏥 Clinic Management</h2>
                <p style='margin:8px 0 0;color:rgba(255,255,255,0.84);'>Modern patient scheduling with AI assistance.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        if st.session_state.logged_in:
            st.markdown(f"**Logged in as:** {st.session_state.user['full_name']}")
            st.markdown(f"**Role:** {st.session_state.user['role'].title()}")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = "login"
                st.rerun()
        else:
            st.info("Please log in to continue")


# ============ AUTHENTICATION PAGES ============

def login_page():
    """User login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🏥 Patient Appointment Tracker")
        st.subheader("Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        st.text_area("Test Account Information", value="Doctor: doctor123@clinic.com Password: password123\nPatient: patient123@clinic.com Password: password123", height=100)

        if st.button("Login", use_container_width=True):
            result = login_user(email, password)
            if result["success"]:
                st.session_state.logged_in = True
                st.session_state.user = result["user"]
                st.session_state.page = "dashboard"
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(result["message"])
        
        st.divider()
        st.write("Don't have an account?")
        if st.button("Go to Registration", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()


def register_page():
    """User registration page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🏥 Patient Appointment Tracker")
        st.subheader("Create an Account")
        
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        
        role = st.radio("Select Your Role", ["patient", "doctor"])
        
        if st.button("Register", use_container_width=True):
            if not full_name or not email or not password:
                st.error("Please fill in all fields")
            elif password != password_confirm:
                st.error("Passwords do not match")
            else:
                result = register_user(email, password, full_name, role)
                if result["success"]:
                    st.success(result["message"])
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(result["message"])
        
        st.divider()
        if st.button("Back to Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ============ PATIENT DASHBOARD ============

def patient_dashboard():
    """Patient dashboard with booking and appointment management"""
    st.markdown(
        """
        <div class='section-header'>
          <h1>📋 Patient Dashboard</h1>
          <p>Manage your appointments, ask the AI assistant, and stay informed in one place.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(f"Welcome back, {st.session_state.user['full_name']}!")
    
    patient_email = st.session_state.user["email"]
    
    # Tabs for different patient functions
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📅 Book Appointment", "📝 My Appointments", "💬 Ask Assistant", "ℹ️ Instructions"]
    )
    
    # ========== TAB 1: BOOK APPOINTMENT ==========
    with tab1:
        st.subheader("Book an Appointment")
        
        # Get available slots from doctors
        schedules = load_schedules()
        available_slots = [s for s in schedules["schedules"] if s["status"] == "available"]
        
        if available_slots:
            # Group slots by doctor
            doctors = {}
            for slot in available_slots:
                if slot["doctor_email"] not in doctors:
                    doctors[slot["doctor_email"]] = []
                doctors[slot["doctor_email"]].append(slot)
            
            # Select doctor
            doctor_email = st.selectbox(
                "Select Doctor",
                options=list(doctors.keys()),
                format_func=lambda x: x.split("@")[0].title()
            )
            
            if doctor_email:
                doctor_slots = doctors[doctor_email]
                
                # Create display options
                slot_options = [
                    f"{slot['date']} at {slot['time']} ({slot['duration_minutes']} min)"
                    for slot in doctor_slots
                ]
                
                selected_slot_display = st.selectbox("Select Time Slot", slot_options)
                selected_slot_index = slot_options.index(selected_slot_display)
                selected_slot = doctor_slots[selected_slot_index]
                
                if st.button("Book Appointment", use_container_width=True):
                    result = book_appointment(
                        patient_email,
                        st.session_state.user["full_name"],
                        selected_slot["slot_id"]
                    )
                    if result["success"]:
                        st.success(f"✅ {result['message']}\nAppointment ID: {result['appointment_id']}")
                    else:
                        st.error(result["message"])
        else:
            st.info("No available time slots at the moment. Please check back later!")

        with st.expander("📆 Weekly Availability Calendar", expanded=True):
            selected_week = st.date_input("Choose week starting", value=datetime.now().date(), key="patient_calendar_week")
            week_dates = get_week_dates(selected_week)
            day_slots = get_slots_by_day(available_slots)
            calendar_cols = st.columns(7)

            for date_obj, col in zip(week_dates, calendar_cols):
                day_key = date_obj.strftime("%Y-%m-%d")
                with col:
                    st.markdown(f"**{date_obj.strftime('%a')}**<br>{date_obj.strftime('%b %d')}", unsafe_allow_html=True)
                    slots_for_day = day_slots.get(day_key, [])
                    if slots_for_day:
                        for slot in slots_for_day:
                            label = f"{slot['time']} ({slot['duration_minutes']}m)"
                            if st.button(label, key=f"book_calendar_{slot['slot_id']}", use_container_width=True):
                                result = book_appointment(patient_email, st.session_state.user["full_name"], slot["slot_id"])
                                if result["success"]:
                                    st.success(f"{result['message']} Appointment ID: {result['appointment_id']}")
                                    st.rerun()
                                else:
                                    st.error(result["message"])
                    else:
                        st.write("No slots")
    
    # ========== TAB 2: MY APPOINTMENTS ==========
    with tab2:
        st.subheader("My Appointments")
        
        appointments = get_patient_appointments(patient_email)
        
        if appointments:
            for apt in appointments:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Date & Time:** {apt['date']} at {apt['time']}")
                        st.write(f"**Doctor:** {apt['doctor_email'].split('@')[0].title()}")
                        st.write(f"**Status:** {apt['status'].upper()}")
                        if apt['notes']:
                            st.write(f"**Notes:** {apt['notes']}")
                    
                    with col2:
                        if apt['status'] == 'booked':
                            if st.button("Cancel", key=f"cancel_{apt['appointment_id']}", use_container_width=True):
                                result = cancel_appointment(apt['appointment_id'])
                                if result["success"]:
                                    st.success("Appointment cancelled")
                                    st.rerun()
                    
                    with col3:
                        if apt['status'] == 'booked':
                            if st.button("Reschedule", key=f"reschedule_{apt['appointment_id']}", use_container_width=True):
                                st.session_state.reschedule_apt_id = apt['appointment_id']
        else:
            st.info("You don't have any appointments yet. Book one in the 'Book Appointment' tab!")
    
    # ========== TAB 3: CHATBOT ASSISTANT ==========
    with tab3:
        st.subheader("💬 AI Assistant")
        st.write("Ask questions about your appointments and clinic services. The assistant uses your appointment data to answer.")

        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
            logs = ChatLoggerStore(CHAT_LOGS_FILE).load_logs()
            for log in logs:
                if isinstance(log, dict) and "user_message" in log and "assistant_message" in log:
                    st.session_state.chat_messages.append({"role": "user", "content": log["user_message"]})
                    st.session_state.chat_messages.append({"role": "assistant", "content": log["assistant_message"]})

        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        user_input = st.chat_input("Ask the clinic assistant…")
        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            assistant_response = get_ai_assistant_response(
                user_input,
                patient_email,
                st.session_state.chat_messages
            )
            st.session_state.chat_messages.append({"role": "assistant", "content": assistant_response})

            chat_logger = ChatLoggerStore(CHAT_LOGS_FILE)
            logs = chat_logger.load_logs()
            logs.append({"user_message": user_input, "assistant_message": assistant_response})
            chat_logger.save_logs(logs)

            st.rerun()

    # ========== TAB 4: INSTRUCTIONS ==========
    with tab4:
        st.subheader("How to Use")
        st.markdown("""
        ### Patient Features:
        
        1. **Book Appointment**
           - Select a doctor from the list
           - Choose an available time slot
           - Click "Book Appointment" to confirm
        
        2. **Manage Appointments**
           - View all your booked appointments
           - Cancel an appointment if needed
           - Reschedule to a different time
        
        3. **Ask Questions**
           - Use the AI Assistant tab to ask common questions
           - The assistant can help with appointment info and clinic policies
        
        4. **Appointment Status**
           - Booked: Your confirmed appointment
           - Completed: Finished appointment
           - No-Show: You missed the appointment
           - Cancelled: Appointment was cancelled
        """)


# ============ DOCTOR DASHBOARD ============

def doctor_dashboard():
    """Doctor/Admin dashboard with schedule and appointment management"""
    st.markdown(
        """
        <div class='section-header'>
          <h1>👨‍⚕️ Doctor Dashboard</h1>
          <p>Organize your schedule, manage patients, and track clinic performance.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(f"Welcome, Dr. {st.session_state.user['full_name']}!")
    
    doctor_email = st.session_state.user["email"]
    
    # Tabs for doctor functions
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📅 Manage Schedule", "👥 Patient Roster", "ℹ️ Instructions", "📊 Statistics"]
    )
    
    # ========== TAB 1: MANAGE SCHEDULE ==========
    with tab1:
        st.subheader("Manage Your Schedule")
        
        # Create new time slot
        st.write("### Create New Time Slot")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            slot_date = st.date_input("Date", min_value=datetime.now().date())
        with col2:
            slot_time = st.time_input("Time", value=datetime.strptime("09:00", "%H:%M").time())
        with col3:
            duration = st.number_input("Duration (minutes)", value=30, min_value=15, max_value=120, step=15)
        with col4:
            if st.button("Create Slot", use_container_width=True):
                result = create_time_slot(
                    doctor_email,
                    slot_date.strftime("%Y-%m-%d"),
                    slot_time.strftime("%H:%M"),
                    duration
                )
                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    st.rerun()
                else:
                    st.error(result["message"])
        
        st.divider()

        with st.expander("⚙️ Advanced Scheduling", expanded=False):
            weekday_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            selected_weekdays = st.multiselect("Repeat on", weekday_options, default=[weekday_options[0]])
            recurring_start = st.date_input("Start Date", value=datetime.now().date(), key="recurring_start")
            recurring_end = st.date_input("End Date", value=datetime.now().date() + timedelta(days=28), key="recurring_end")
            recurring_time = st.time_input("Slot Time", value=datetime.strptime("09:00", "%H:%M").time(), key="recurring_slot_time")
            recurring_duration = st.number_input("Duration (minutes)", value=30, min_value=15, max_value=120, step=15, key="recurring_duration")
            recurring_frequency = st.selectbox("Repeat every", ["1 week", "2 weeks"], key="recurring_frequency")

            if st.button("Create recurring slots", use_container_width=True):
                weekdays_int = [weekday_options.index(day) for day in selected_weekdays]
                frequency_weeks = 1 if recurring_frequency == "1 week" else 2
                result = create_recurring_slots(
                    doctor_email,
                    recurring_start,
                    recurring_end,
                    weekdays_int,
                    recurring_time.strftime("%H:%M"),
                    recurring_duration,
                    frequency_weeks
                )
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])

        with st.expander("📅 Weekly Schedule Calendar", expanded=True):
            schedule_week = st.date_input("Week of", value=datetime.now().date(), key="doctor_calendar_week")
            weekly_dates = get_week_dates(schedule_week)
            schedule = get_doctor_schedule(doctor_email)
            schedule_by_day = get_slots_by_day(schedule)
            day_columns = st.columns(7)

            for date_obj, col in zip(weekly_dates, day_columns):
                with col:
                    st.markdown(f"**{date_obj.strftime('%a %d %b')}**")
                    slots_for_day = schedule_by_day.get(date_obj.strftime("%Y-%m-%d"), [])
                    if slots_for_day:
                        for slot in slots_for_day:
                            status_badge = "🟢" if slot['status'] == 'available' else "🔴"
                            st.write(f"{status_badge} {slot['time']} ({slot['duration_minutes']}m)")
                    else:
                        st.write("No slots")

        # View and delete time slots
        st.write("### Your Available Time Slots")
        schedule = get_doctor_schedule(doctor_email)
        
        if schedule:
            for slot in schedule:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Date & Time:** {slot['date']} at {slot['time']}")
                        st.write(f"**Duration:** {slot['duration_minutes']} minutes")
                        status_color = "🟢" if slot['status'] == "available" else "🔴"
                        st.write(f"**Status:** {status_color} {slot['status'].upper()}")
                    
                    with col2:
                        if slot['status'] == 'available':
                            if st.button("Delete", key=f"delete_{slot['slot_id']}", use_container_width=True):
                                result = delete_time_slot(slot['slot_id'])
                                if result["success"]:
                                    st.success("Slot deleted")
                                    st.rerun()
        else:
            st.info("No time slots created yet. Create one above!")
    
    # ========== TAB 2: PATIENT ROSTER ==========
    with tab2:
        st.subheader("Today's Patient Roster")
        
        appointments = get_doctor_appointments(doctor_email)
        today = datetime.now().strftime("%Y-%m-%d")
        today_appointments = [a for a in appointments if a['date'] == today]
        
        if today_appointments:
            for apt in today_appointments:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Patient:** {apt['patient_name']}")
                        st.write(f"**Email:** {apt['patient_email']}")
                        st.write(f"**Time:** {apt['time']} ({apt['duration_minutes']} min)")
                        st.write(f"**Status:** {apt['status'].upper()}")
                    
                    with col2:
                        new_status = st.selectbox(
                            "Update Status",
                            ["booked", "completed", "no-show"],
                            key=f"status_{apt['appointment_id']}"
                        )
                        if st.button("Update", key=f"update_{apt['appointment_id']}", use_container_width=True):
                            result = update_appointment_status(apt['appointment_id'], new_status)
                            if result["success"]:
                                st.success("Status updated")
                                st.rerun()
                    
                    with col3:
                        notes = st.text_input("Notes", key=f"notes_{apt['appointment_id']}")
                        if st.button("Save Notes", key=f"save_notes_{apt['appointment_id']}", use_container_width=True):
                            result = update_appointment_notes(apt['appointment_id'], notes)
                            if result["success"]:
                                st.success("Notes saved")
        else:
            st.info(f"No appointments scheduled for today ({today})")
        
        # All upcoming appointments
        st.divider()
        st.write("### All Upcoming Appointments")
        upcoming = [a for a in appointments if a['status'] == 'booked']
        if upcoming:
            for apt in upcoming[:10]:  # Show last 10
                with st.container(border=True):
                    st.write(f"{apt['date']} at {apt['time']} - {apt['patient_name']} ({apt['patient_email']})")
        else:
            st.info("No upcoming appointments")
    
    # ========== TAB 3: INSTRUCTIONS ==========
    with tab3:
        st.subheader("How to Use Doctor Dashboard")
        st.markdown("""
        ### Doctor Features:
        
        1. **Manage Schedule**
           - Create available time slots for your schedule
           - Set the date, time, and duration for each slot
           - Delete slots that you need to remove
        
        2. **Patient Roster**
           - View today's appointments in chronological order
           - Update appointment statuses (Completed, No-Show)
           - Add notes about the patient visit
        
        3. **Appointment Status Options**
           - Booked: Appointment is scheduled
           - Completed: Patient was seen and appointment is done
           - No-Show: Patient did not show up
        """)
    
    # ========== TAB 4: STATISTICS ==========
    with tab4:
        st.subheader("Schedule Statistics")
        
        total_slots = len(schedule)
        available_slots_count = len([s for s in schedule if s['status'] == 'available'])
        booked_slots_count = len([s for s in schedule if s['status'] == 'booked'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Slots", total_slots)
        col2.metric("Available", available_slots_count)
        col3.metric("Booked", booked_slots_count)


# ============ MAIN APPLICATION FLOW ============

def main():
    """Main application flow"""
    sidebar_navigation()
    
    if not st.session_state.logged_in:
        if st.session_state.page == "register":
            register_page()
        else:
            login_page()
    else:
        # Route to appropriate dashboard based on role
        if st.session_state.user["role"] == "doctor":
            doctor_dashboard()
        else:
            patient_dashboard()


if __name__ == "__main__":
    main()
