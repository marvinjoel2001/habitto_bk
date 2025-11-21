#!/usr/bin/env python
import os
import sys
import django
import json
from unittest.mock import Mock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bk_habitto.settings')
django.setup()

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.test import APIRequestFactory

def test_simplejwt_directly():
    """Test SimpleJWT TokenObtainPairView directly"""
    
    factory = APIRequestFactory()
    
    # Create a mock request
    request_data = {
        'username': 'carlos_mendoza',
        'password': 'sistemas123'
    }
    
    request = factory.post('/api/login/', 
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    # Create the view
    view = TokenObtainPairView.as_view()
    
    try:
        # Call the view
        response = view(request)
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        if response.status_code == 200:
            print("✓ SimpleJWT login successful!")
            print(f"  - Access token: {response.data.get('access', 'N/A')[:50]}...")
            print(f"  - Refresh token: {response.data.get('refresh', 'N/A')[:50]}...")
        else:
            print("✗ SimpleJWT login failed")
            print(f"  - Error: {response.data}")
            
    except Exception as e:
        print(f"✗ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simplejwt_directly()