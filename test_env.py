#!/usr/bin/env python3
"""Test script to check environment variables"""

import os

def check_env_vars():
    """Check if required environment variables are set"""
    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY", 
        "SECRET_KEY",
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

if __name__ == "__main__":
    check_env_vars() 