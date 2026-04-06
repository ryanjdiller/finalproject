"""
Simple Chatbot module with 5 hardcoded responses
Phase 1: Simulated AI responses for common patient queries
"""

from data_manager import get_patient_appointments


def get_chatbot_response(user_query: str, user_email: str, user_name: str) -> str:
    """
    Get a hardcoded response from the chatbot based on user query
    
    Args:
        user_query: The user's question (converted to lowercase)
        user_email: Email of the user asking
        user_name: Full name of the user
    
    Returns:
        Chatbot response string
    """
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
