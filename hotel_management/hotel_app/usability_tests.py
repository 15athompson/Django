from django.test import TestCase, Client, LiveServerTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
import time
from datetime import datetime, timedelta
from decimal import Decimal

from hotel_app.models import Room, Booking, Guest, Service

class UsabilityTests(TestCase):
    """
    Tests for usability aspects of the hotel management system.
    Focuses on user interface, navigation, and user experience.
    """

    def setUp(self):
        """Set up test data and configurations."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create test guest
        self.guest = Guest.objects.create(
            first_name='Test',
            last_name='User',
            email='test@example.com',
            phone='1234567890'
        )
        
        # Create test rooms
        self.rooms = []
        room_types = ['single', 'double', 'suite', 'deluxe']
        for i in range(4):
            room = Room.objects.create(
                number=f'10{i}',
                room_type=room_types[i],
                capacity=i + 1,
                price=Decimal(100 * (i + 1)),
                description=f'Test Room {i + 1}',
                is_available=True
            )
            self.rooms.append(room)

        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_navigation_flow(self):
        """
        Test the natural navigation flow through the application.
        """
        # Start at home page
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        # Navigate to room list
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)

        # View room detail
        response = self.client.get(reverse('room_detail', args=[self.rooms[0].id]))
        self.assertEqual(response.status_code, 200)

        # Access booking form
        response = self.client.get(
            reverse('booking_form'), 
            {'room_id': self.rooms[0].id}
        )
        self.assertEqual(response.status_code, 200)

        # View bookings list
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)

    def test_form_validation_feedback(self):
        """
        Test that forms provide clear feedback for validation errors.
        """
        # Test invalid booking dates
        response = self.client.post(reverse('booking_form'), {
            'room': self.rooms[0].id,
            'check_in': timezone.now().date(),
            'check_out': timezone.now().date() - timedelta(days=1),
            'guests': 1
        })
        self.assertEqual(response.status_code, 200)

        # Test exceeding room capacity
        response = self.client.post(reverse('booking_form'), {
            'room': self.rooms[0].id,
            'check_in': timezone.now().date(),
            'check_out': timezone.now().date() + timedelta(days=1),
            'guests': self.rooms[0].capacity + 1
        })
        self.assertEqual(response.status_code, 200)

        # Test missing required fields
        response = self.client.post(reverse('booking_form'), {})
        self.assertEqual(response.status_code, 200)

    def test_search_functionality(self):
        """
        Test the usability of search and filter functions.
        """
        # Test search by room type
        response = self.client.get(reverse('room_list'), {'room_type': 'deluxe'})
        self.assertEqual(response.status_code, 200)

        # Test search by date range
        check_in = timezone.now().date()
        check_out = check_in + timedelta(days=1)
        response = self.client.get(reverse('room_list'), {
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 200)

        # Test search by number of guests
        response = self.client.get(reverse('room_list'), {'guests': 2})
        self.assertEqual(response.status_code, 200)

        # Test combined search
        response = self.client.get(reverse('room_list'), {
            'room_type': 'double',
            'guests': 2,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 200)

    def test_responsive_design(self):
        """
        Test page rendering with different viewport sizes.
        """
        # Test mobile viewport
        self.client.defaults['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)

        # Test tablet viewport
        self.client.defaults['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)'
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)

        # Test desktop viewport
        self.client.defaults['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)

    def test_error_handling(self):
        """
        Test how the system handles and displays errors to users.
        """
        # Test invalid room ID
        response = self.client.get(reverse('room_detail', args=[999]))
        self.assertEqual(response.status_code, 404)

        # Test invalid booking ID
        response = self.client.get(reverse('booking_confirmation', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_booking_workflow(self):
        """
        Test the complete booking workflow from start to finish.
        """
        # Step 1: View available rooms
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)

        # Step 2: Select a room
        room = self.rooms[0]
        response = self.client.get(reverse('room_detail', args=[room.id]))
        self.assertEqual(response.status_code, 200)

        # Step 3: Start booking process
        response = self.client.get(reverse('booking_form'), {'room_id': room.id})
        self.assertEqual(response.status_code, 200)

        # Step 4: Submit booking
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)
        response = self.client.post(reverse('booking_form'), {
            'room': room.id,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'guests': room.capacity,
            'special_requests': 'Test booking'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect to confirmation

        # Step 5: View booking confirmation
        booking = Booking.objects.latest('id')
        response = self.client.get(reverse('booking_confirmation', args=[booking.id]))
        self.assertEqual(response.status_code, 200)

    def test_accessibility(self):
        """
        Test basic accessibility features.
        """
        # Test for form labels
        response = self.client.get(reverse('booking_form'))
        self.assertEqual(response.status_code, 200)

        # Test for proper form structure
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_feedback(self):
        """
        Test system feedback for user actions.
        """
        # Test successful booking
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)
        response = self.client.post(reverse('booking_form'), {
            'room': self.rooms[0].id,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'guests': self.rooms[0].capacity,
            'special_requests': 'Test booking'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # Test login
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
