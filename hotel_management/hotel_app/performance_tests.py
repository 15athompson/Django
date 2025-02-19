from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Room, Booking, Guest
from .forms import BookingForm
from django.test.utils import override_settings
import datetime
import time
from django.core.management import call_command

@override_settings(TEST=True)
class PerformanceTests(TestCase):
    def setUp(self):
        call_command('flush', verbosity=0, interactive=False)
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.room = Room.objects.create(
            number=101,
            room_type='Standard',
            price=100.00,
            capacity=2
        )
        self.guest = Guest.objects.create(
            first_name='Test',
            last_name='Guest',
            email='test@example.com',
            phone='1234567890'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_create_room_performance(self):
        start_time = time.time()
        for i in range(100):
            room_number = int(f"{i}")
            response = self.client.post(reverse('room-list'), {
                'number': room_number,
                'room_type': 'Deluxe',
                'price': 200.00,
                'capacity': 4,
                'is_available': True,
                'description': 'Performance test room'
            })
            self.assertEqual(response.status_code, 201)
        end_time = time.time()
        print(f"Time taken to create 100 rooms: {end_time - start_time:.2f} seconds")

    def test_create_booking_performance(self):
        start_time = time.time()
        for i in range(100):
            check_in_date = timezone.now().date() + datetime.timedelta(days=i)
            check_out_date = check_in_date + datetime.timedelta(days=3)
            response = self.client.post(reverse('booking-list'), {
                'room': self.room.id,
                'check_in': check_in_date,
                'check_out': check_out_date,
                'guests': 2
            })
            self.assertEqual(response.status_code, 201)
        end_time = time.time()
        print(f"Time taken to create 100 bookings: {end_time - start_time:.2f} seconds")
