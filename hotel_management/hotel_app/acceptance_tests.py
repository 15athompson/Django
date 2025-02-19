from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json

from hotel_app.models import Room, Booking, Guest, Service

class AcceptanceTests(TestCase):
    """
    Acceptance tests for the hotel booking system.
    Tests user stories and acceptance criteria from an end-user perspective.
    """

    def setUp(self):
        """Set up test data and configurations."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
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

    def test_room_search_and_filtering(self):
        """
        User Story: As a user, I want to search and filter rooms
        so that I can find suitable accommodation.
        """
        self.client.login(username='testuser', password='testpass123')

        # Test basic room listing
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['rooms']) > 0)

        # Test room type filter
        response = self.client.get(reverse('room_list'), {'room_type': 'deluxe'})
        self.assertEqual(response.status_code, 200)
        for room in response.context['rooms']:
            self.assertEqual(room.room_type, 'deluxe')

        # Test capacity filter
        response = self.client.get(reverse('room_list'), {'guests': 2})
        self.assertEqual(response.status_code, 200)
        for room in response.context['rooms']:
            self.assertGreaterEqual(room.capacity, 2)

        # Test date availability filter
        check_in = timezone.now().date()
        check_out = check_in + timedelta(days=2)
        response = self.client.get(reverse('room_list'), {
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 200)

    def test_complete_booking_process(self):
        """
        User Story: As a logged-in user, I want to complete a room booking
        so that I can reserve accommodation.
        """
        self.client.login(username='testuser', password='testpass123')

        # Step 1: View available rooms
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)

        # Step 2: Select a room
        room = self.rooms[0]
        response = self.client.get(reverse('room_detail', args=[room.id]))
        self.assertEqual(response.status_code, 200)

        # Step 3: Make a booking
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)
        booking_data = {
            'room': room.id,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'guests': 1,
            'special_requests': 'Test booking'
        }
        response = self.client.post(reverse('booking_form'), booking_data)
        self.assertIn(response.status_code, [200, 302])

        # Step 4: Verify booking in user's booking list
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['bookings']) > 0)

    def test_room_availability_updates(self):
        """
        User Story: As a user, I want to see real-time room availability
        so that I can make informed booking decisions.
        """
        self.client.login(username='testuser', password='testpass123')

        room = self.rooms[0]
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)

        # Check initial availability
        response = self.client.get(reverse('room_detail', args=[room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(room.is_available)

        # Make a booking
        Booking.objects.create(
            guest=self.user,
            room=room,
            check_in=check_in,
            check_out=check_out,
            guests=1
        )

        # Verify room shows as unavailable for those dates
        response = self.client.get(reverse('room_list'), {
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(room, response.context['rooms'])

    def test_booking_validation(self):
        """
        User Story: As a user, I want to receive clear validation messages
        so that I can correct any booking errors.
        """
        self.client.login(username='testuser', password='testpass123')

        # Test booking with invalid dates
        room = self.rooms[0]
        invalid_booking = {
            'room': room.id,
            'check_in': timezone.now().date(),
            'check_out': timezone.now().date() - timedelta(days=1),
            'guests': 1,
            'special_requests': 'Test booking'
        }
        response = self.client.post(reverse('booking_form'), invalid_booking)
        self.assertEqual(response.status_code, 200)

        # Test booking with too many guests
        invalid_booking = {
            'room': room.id,
            'check_in': timezone.now().date(),
            'check_out': timezone.now().date() + timedelta(days=1),
            'guests': room.capacity + 1,
            'special_requests': 'Test booking'
        }
        response = self.client.post(reverse('booking_form'), invalid_booking)
        self.assertEqual(response.status_code, 200)

    def test_booking_list_view(self):
        """
        User Story: As a user, I want to view my bookings
        so that I can track my reservations.
        """
        self.client.login(username='testuser', password='testpass123')

        # Create some test bookings
        for room in self.rooms[:2]:
            Booking.objects.create(
                guest=self.user,
                room=room,
                check_in=timezone.now().date() + timedelta(days=1),
                check_out=timezone.now().date() + timedelta(days=3),
                guests=1
            )

        # View booking list
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['bookings']), 2)

    def test_room_detail_view(self):
        """
        User Story: As a user, I want to view room details
        so that I can make informed booking decisions.
        """
        self.client.login(username='testuser', password='testpass123')

        room = self.rooms[0]
        response = self.client.get(reverse('room_detail', args=[room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['room'], room)
