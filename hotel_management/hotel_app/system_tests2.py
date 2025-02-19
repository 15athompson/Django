from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Room, Booking 

class SystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'systemtestuser'
        self.password = 'systemtestpass123'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password
        )
        self.room = Room.objects.create(
            number=301,
            room_type='Suite',
            price=300.00,
            capacity=4
        )

    def test_user_registration_login(self):
        # Registration (assuming you have a registration view)
        # response = self.client.post(reverse('register'), {
        #     'username': 'newuser',
        #     'password': 'newpassword',
        #     'password_confirm': 'newpassword'
        # })
        # self.assertEqual(response.status_code, 302)  # Redirect after successful registration

        # Login
        login_successful = self.client.login(username=self.username, password=self.password)
        self.assertTrue(login_successful)
        response = self.client.get(reverse('home'))  # Assuming 'home' is the home page after login
        self.assertEqual(response.status_code, 200)

    def test_room_booking(self):
        self.client.login(username=self.username, password=self.password)
        # Get booking form
        response = self.client.get(reverse('booking_form'))
        self.assertEqual(response.status_code, 200)

        # Post booking data
        booking_data = {
            'room': self.room.id,
            'check_in': '2025-03-10',
            'check_out': '2025-03-15',
            'guests': 2,
            'guest_id': self.user.id  # Explicitly set the guest_id
        }
        response = self.client.post(reverse('booking_form'), booking_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Booking Confirmed!')  # Or some other success message

        # Check if booking exists and is associated with the correct user
        booking = Booking.objects.filter(room=self.room, guest=self.user).first()
        self.assertTrue(booking is not None)

    def test_viewing_booking_list(self):
        from bs4 import BeautifulSoup

        # Login the user
        self.client.login(username=self.username, password=self.password)

        # Create a booking
        booking_data = {
            'room': self.room.id,
            'check_in': '2025-03-10',
            'check_out': '2025-03-15',
            'guests': 2,
            'guest_id': self.user.id  # Explicitly set the guest_id
        }
        self.client.post(reverse('booking_form'), booking_data, follow=True)

        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)

        # Parse the HTML response
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check if the room type is present in the parsed HTML
        room_type_present = self.room.room_type in soup.prettify()
        self.assertTrue(room_type_present)

    def test_admin_panel_access(self):
        # Create a superuser
        admin_user = User.objects.create_superuser(
            username='adminuser',
            password='adminpass123',
            email='admin@example.com'
        )
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('admin:index'))  # Admin index page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django administration')
