"""
Patient Appointment Tracker - Streamlit MVP
Main application file with authentication, role-based dashboards, and CRUD operations
"""

import streamlit as st
from datetime import datetime, timedelta
import json

from auth import register_user, login_user
from data_manager import (
    create_time_slot, get_doctor_schedule, get_available_slots, delete_time_slot,
    book_appointment, get_patient_appointments, get_doctor_appointments,
    cancel_appointment, reschedule_appointment, update_appointment_status, update_appointment_notes
)
from chatbot import get_chatbot_response


# ============ PAGE CONFIG AND INITIALIZATION ============

st.set_page_config(page_title="Patient Appointment Tracker", layout="wide")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "login"


# ============ SIDEBAR NAVIGATION ============

def sidebar_navigation():
    """Render sidebar with navigation and logout"""
    with st.sidebar:
        st.title("🏥 Clinic Management")
        
        if st.session_state.logged_in:
            st.write(f"**Logged in as:** {st.session_state.user['full_name']}")
            st.write(f"**Role:** {st.session_state.user['role'].title()}")
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = "login"
                st.rerun()
        else:
            st.write("Please log in to continue")


# ============ AUTHENTICATION PAGES ============

def login_page():
    """User login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🏥 Patient Appointment Tracker")
        st.subheader("Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
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
    st.title("📋 Patient Dashboard")
    st.write(f"Welcome, {st.session_state.user['full_name']}!")
    
    patient_email = st.session_state.user["email"]
    
    # Tabs for different patient functions
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📅 Book Appointment", "📝 My Appointments", "💬 Ask Assistant", "ℹ️ Instructions"]
    )
    
    # ========== TAB 1: BOOK APPOINTMENT ==========
    with tab1:
        st.subheader("Book an Appointment")
        
        # Get available slots from doctors
        from data_manager import load_schedules
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
        st.write("Ask me common questions about your appointments and the clinic!")
        
        user_question = st.text_area("Your Question", placeholder="e.g., When is my next appointment?")
        
        if st.button("Ask Assistant", use_container_width=True):
            if user_question:
                response = get_chatbot_response(user_question, patient_email, st.session_state.user["full_name"])
                st.info(response)
    
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
    st.title("👨‍⚕️ Doctor Dashboard")
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
