"""
Data manager module for appointment and schedule management
Handles all JSON-based data operations
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

APPOINTMENTS_FILE = "appointments.json"
SCHEDULES_FILE = "schedules.json"


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


# ============ SCHEDULE MANAGEMENT (Doctor/Admin CRUD) ============

def create_time_slot(doctor_email: str, date: str, time: str, duration_minutes: int = 30) -> dict:
    """
    Create an available time slot for a doctor
    
    Args:
        doctor_email: Doctor's email
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format
        duration_minutes: Duration of the slot
    
    Returns:
        dict with success status
    """
    schedules = load_schedules()
    
    slot_id = f"{doctor_email}_{date}_{time}".replace(" ", "_").replace(":", "-")
    
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


# ============ APPOINTMENT MANAGEMENT (Both Roles CRUD) ============

def book_appointment(patient_email: str, patient_name: str, slot_id: str) -> dict:
    """
    Book an appointment for a patient
    
    Args:
        patient_email: Patient's email
        patient_name: Patient's full name
        slot_id: The time slot ID to book
    
    Returns:
        dict with success status
    """
    schedules = load_schedules()
    
    # Find the time slot
    slot = next((s for s in schedules["schedules"] if s["slot_id"] == slot_id), None)
    if not slot or slot["status"] != "available":
        return {"success": False, "message": "Time slot not available"}
    
    # Create appointment
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
    
    # Mark slot as booked
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
    
    # Find and cancel the appointment
    appointment = next((a for a in appointments["appointments"] 
                       if a["appointment_id"] == appointment_id), None)
    
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    appointment["status"] = "cancelled"
    save_appointments(appointments)
    
    # Free up the slot
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
    
    # Find appointment
    appointment = next((a for a in appointments["appointments"] 
                       if a["appointment_id"] == appointment_id), None)
    
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    # Find new slot
    new_slot = next((s for s in schedules["schedules"] if s["slot_id"] == new_slot_id), None)
    
    if not new_slot or new_slot["status"] != "available":
        return {"success": False, "message": "New time slot not available"}
    
    # Free up old slot
    old_slot_id = f"{appointment['doctor_email']}_{appointment['date']}_{appointment['time']}".replace(" ", "_").replace(":", "-")
    for slot in schedules["schedules"]:
        if slot["slot_id"] == old_slot_id:
            slot["status"] = "available"
    
    # Update appointment
    appointment["date"] = new_slot["date"]
    appointment["time"] = new_slot["time"]
    appointment["duration_minutes"] = new_slot["duration_minutes"]
    
    # Mark new slot as booked
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
