from django.contrib.auth.models import User
from hotel_app.models import UserProfile

for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)
