from django.test import TestCase, Client
from django.urls import reverse
from .models import Room, Booking
import datetime
from django.contrib.auth.models import User

class BookingIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.room = Room.objects.create(
            number=101,
            room_type='Standard',
            price=100.00,
            capacity=2
        )
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    def test_successful_booking(self):
        # Simulate user submitting the booking form
        check_in_date = datetime.date(2025, 3, 10)
        check_out_date = datetime.date(2025, 3, 15)
        response = self.client.post(reverse('booking_form'), {
            'room': self.room.id,
            'check_in': check_in_date,
            'check_out': check_out_date,
            'guests': 2
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        # Check if a booking object is created in the database
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.room, self.room)
        self.assertEqual(booking.guests, 2)
