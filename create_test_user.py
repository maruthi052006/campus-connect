import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campusconnect.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    User.objects.filter(username='test_flow_user').delete()
    u = User.objects.create_user(username='test_flow_user', password='password123', email='test@test.com')
    # Assuming role is needed
    u.is_first_login = True
    u.is_profile_setup = False
    u.save()
    print("SUCCESS: User created")
except Exception as e:
    import traceback
    traceback.print_exc()
