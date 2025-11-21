#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bk_habitto.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

def debug_login():
    """Debug the login issue for carlos_mendoza"""

    # Check if user exists
    try:
        user = User.objects.get(username='carlos_mendoza')
        print(f"✓ User found: {user}")
        print(f"  - Username: {user.username}")
        print(f"  - Email: {user.email}")
        print(f"  - Is active: {user.is_active}")
        print(f"  - Is staff: {user.is_staff}")
        print(f"  - Is superuser: {user.is_superuser}")
        print(f"  - Date joined: {user.date_joined}")
        print(f"  - Last login: {user.last_login}")

        # Check password
        password_correct = user.check_password('sistemas123')
        print(f"  - Password correct: {password_correct}")

        if password_correct and user.is_active:
            # Try to generate tokens
            try:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                print(f"\n✓ Token generation successful:")
                print(f"  - Access token (first 50 chars): {access_token[:50]}...")
                print(f"  - Refresh token (first 50 chars): {refresh_token[:50]}...")

                # Test token validation
                from rest_framework_simplejwt.tokens import AccessToken
                try:
                    validated_token = AccessToken(access_token)
                    print(f"  - Token validation: SUCCESS")
                    print(f"  - User ID from token: {validated_token['user_id']}")
                except Exception as e:
                    print(f"  - Token validation: FAILED - {e}")

            except Exception as e:
                print(f"\n✗ Token generation failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n✗ User cannot login - Active: {user.is_active}, Password correct: {password_correct}")

    except User.DoesNotExist:
        print(f"✗ User 'carlos_mendoza' not found")

        # List all users
        print("\nAvailable users:")
        for u in User.objects.all()[:10]:
            print(f"  - {u.username} ({u.email}) - Active: {u.is_active}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_login()
