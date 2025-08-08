# make_admin.py
from django.contrib.auth import get_user_model

User = get_user_model()
username = 'admin2'  # pick a new username
email = 'engr.mohammadhamzanadeem@gmail.com'
password = 'new_password'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Admin created!")
else:
    print("User already exists.")
