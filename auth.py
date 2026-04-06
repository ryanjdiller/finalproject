"""
Authentication module for Patient Appointment Tracker
Handles user registration, login, and session management
"""

import json
import hashlib
import os
from datetime import datetime

USERS_FILE = "users.json"


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
