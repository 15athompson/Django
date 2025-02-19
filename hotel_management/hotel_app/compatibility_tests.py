from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
from datetime import datetime, timedelta
from decimal import Decimal
import csv
import io

from hotel_app.models import Room, Booking, Guest, Service

class CompatibilityTests(TestCase):
    """
    Tests for system compatibility across different browsers, data formats,
    and API versions.
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

        # Create test booking
        self.booking = Booking.objects.create(
            guest=self.user,
            room=self.rooms[0],
            check_in=timezone.now().date(),
            check_out=timezone.now().date() + timedelta(days=2),
            guests=1
        )

        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_browser_compatibility(self):
        """
        Test system compatibility with different browsers.
        """
        browsers = {
            'Chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Edge': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
            'Mobile': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        }

        test_urls = [
            reverse('home'),
            reverse('room_list'),
            reverse('booking_form'),
            reverse('booking_list'),
        ]

        for browser_name, user_agent in browsers.items():
            self.client.defaults['HTTP_USER_AGENT'] = user_agent
            for url in test_urls:
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 
                    200, 
                    f"Failed to load {url} in {browser_name}"
                )

    def test_data_format_compatibility(self):
        """
        Test system compatibility with different data formats.
        """
        # Test standard GET request
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)
        
        # Test form data submission
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)
        form_data = {
            'room': self.rooms[0].id,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'guests': 1,
            'special_requests': 'Test booking'
        }
        response = self.client.post(
            reverse('booking_form'),
            form_data
        )
        self.assertEqual(response.status_code, 200)

        # Test with JSON content type
        json_data = json.dumps(form_data)
        response = self.client.post(
            reverse('booking_form'),
            json_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_api_version_compatibility(self):
        """
        Test API endpoint compatibility across different versions.
        """
        # Test standard endpoints
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)

        # Test with different accept headers
        headers = {
            'HTTP_ACCEPT': 'application/json',
        }
        response = self.client.get(reverse('room_list'), **headers)
        self.assertEqual(response.status_code, 200)

    def test_date_format_compatibility(self):
        """
        Test compatibility with different date formats.
        """
        date_formats = [
            '%Y-%m-%d',      # 2023-12-31
            '%d/%m/%Y',      # 31/12/2023
            '%m/%d/%Y',      # 12/31/2023
            '%d-%m-%Y',      # 31-12-2023
            '%Y/%m/%d'       # 2023/12/31
        ]

        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)

        for date_format in date_formats:
            form_data = {
                'room': self.rooms[0].id,
                'check_in': check_in.strftime(date_format),
                'check_out': check_out.strftime(date_format),
                'guests': 1
            }
            response = self.client.post(reverse('booking_form'), form_data)
            self.assertIn(response.status_code, [200, 302])

    def test_character_encoding_compatibility(self):
        """
        Test compatibility with different character encodings.
        """
        special_chars = {
            'unicode': 'Test Booking with Unicode: üñîçødé',
            'emoji': 'Test Booking with Emoji: 🏨 🛎️ 🛏️',
            'special': 'Test Booking with Special Chars: ©®™',
            'accents': 'Test Booking with Accents: éèêë',
        }

        for char_type, test_string in special_chars.items():
            # Test in room description
            room = Room.objects.create(
                number=f'special_{char_type}',
                room_type='single',
                capacity=2,
                price=Decimal('100.00'),
                description=test_string,
                is_available=True
            )
            
            # Test in booking special requests
            booking = Booking.objects.create(
                guest=self.user,
                room=room,
                check_in=timezone.now().date(),
                check_out=timezone.now().date() + timedelta(days=1),
                guests=1,
                special_requests=test_string
            )

            # Verify data integrity
            saved_room = Room.objects.get(id=room.id)
            saved_booking = Booking.objects.get(id=booking.id)
            
            self.assertEqual(saved_room.description, test_string)
            self.assertEqual(saved_booking.special_requests, test_string)

    def test_data_export_compatibility(self):
        """
        Test compatibility of data export formats.
        """
        # Test standard HTML response
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)

        # Test with JSON accept header
        response = self.client.get(
            reverse('booking_list'),
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_input_validation_compatibility(self):
        """
        Test compatibility with different input formats and validation.
        """
        test_inputs = {
            'numbers': {
                'valid': ['1', '2', '3', '01', '+1'],
                'invalid': ['abc', '$100', '1.2.3']
            },
            'dates': {
                'valid': ['2023-12-31', '2023/12/31', '31/12/2023'],
                'invalid': ['invalid', '2023-13-01', '00/00/0000']
            },
            'phone': {
                'valid': ['1234567890', '+1-123-456-7890', '(123) 456-7890'],
                'invalid': ['invalid', '123', 'abc-def-ghij']
            }
        }

        for input_type, test_cases in test_inputs.items():
            for valid_input in test_cases['valid']:
                if input_type == 'numbers':
                    response = self.client.get(
                        reverse('room_list'),
                        {'guests': valid_input}
                    )
                    self.assertEqual(response.status_code, 200)
                elif input_type == 'dates':
                    response = self.client.get(
                        reverse('room_list'),
                        {'check_in': valid_input}
                    )
                    self.assertEqual(response.status_code, 200)

    def test_response_header_compatibility(self):
        """
        Test compatibility with different response headers.
        """
        # Test different accept headers
        accept_headers = [
            'text/html',
            'application/json',
            '*/*'
        ]

        for accept in accept_headers:
            response = self.client.get(
                reverse('room_list'),
                HTTP_ACCEPT=accept
            )
            self.assertEqual(response.status_code, 200)

        # Test form submission
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)
        form_data = {
            'room': self.rooms[0].id,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'guests': 1,
            'special_requests': 'Test booking'
        }

        # Test with standard form submission
        response = self.client.post(
            reverse('booking_form'),
            form_data
        )
        self.assertEqual(response.status_code, 200)

        # Test with JSON content type
        json_data = json.dumps(form_data)
        response = self.client.post(
            reverse('booking_form'),
            json_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
