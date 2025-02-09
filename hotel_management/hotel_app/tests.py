from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Room, Booking, Guest
from .forms import BookingForm
from .middleware import AdminLogoutCSRFMiddleware
import datetime

class ModelTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            number=101,
            room_type='Standard',
            price=100.00,
            capacity=2
        )
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.guest = Guest.objects.create(
            first_name='Test',
            last_name='Guest',
            email='test@example.com',
            phone='1234567890'
        )
        self.booking = Booking.objects.create(
            room=self.room,
            guest=self.user,
            check_in=timezone.now().date(),
            check_out=timezone.now().date() + datetime.timedelta(days=3),
            guests=2
        )

    def test_room_creation(self):
        self.assertEqual(self.room.number, 101)
        self.assertEqual(str(self.room), f'Room {self.room.number} - {self.room.room_type}')

    def test_booking_dates(self):
        self.assertTrue(self.booking.check_out > self.booking.check_in)
        

class ViewTests(TestCase):
    def setUp(self):
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

    def test_room_list_view(self):
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Standard')

    def test_booking_view_requires_login(self):
        response = self.client.get(reverse('booking_form'))
        self.assertRedirects(response, f'/login/?next=/booking/')

    def test_authenticated_booking_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('booking_form'))
        self.assertEqual(response.status_code, 200)

class FormTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            number=201,
            room_type='Deluxe',
            price=200.00,
            capacity=4
        )

    def test_valid_booking_form(self):
        form_data = {
            'room': self.room.id,
            'check_in': '2025-03-01',
            'check_out': '2025-03-05',
            'guests': 2
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_date_range(self):
        form_data = {
            'room': self.room.id,
            'check_in': '2025-03-05',
            'check_out': '2025-03-01',
            'guests': 2
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Check-out date must be after check-in date', form.errors['__all__'][0])

class MiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.middleware = AdminLogoutCSRFMiddleware(get_response=lambda req: None)

    def test_logout_redirect_with_csrf(self):
        # Simulate admin logout POST request
        response = self.middleware.process_response(
        request=type('', (), {
            'path': '/admin/logout/',
            'method': 'POST',
            'META': {'CSRF_COOKIE': 'testtoken'},
            'session': {}
        })(),
            response=type('', (), {'status_code': 200})()
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('csrftoken', response.cookies)
