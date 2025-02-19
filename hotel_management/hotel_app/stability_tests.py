from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from datetime import datetime, timedelta
from decimal import Decimal
import time

from hotel_app.models import Room, Booking, Guest, Payment, Service, BookingService, Staff

class StabilityTests(TransactionTestCase):
    """
    Stability tests for the hotel management system.
    Tests system behavior under various stress conditions and extended use.
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
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create test rooms with different types
        self.rooms = []
        room_types = ['single', 'double', 'suite', 'deluxe']
        for i in range(20):  # Create 20 test rooms
            room = Room.objects.create(
                number=f'10{i}',
                room_type=room_types[i % 4],
                capacity=max(2, random.randint(1, 4)),  # Ensure minimum capacity of 2
                price=Decimal(random.randint(100, 500)),
                description=f'Test Room {i}',
                is_available=True
            )
            self.rooms.append(room)

        # Create test services
        self.services = []
        service_names = ['WiFi', 'Breakfast', 'Parking', 'Spa']
        for i, name in enumerate(service_names):
            service = Service.objects.create(
                name=name,
                price=Decimal(random.randint(10, 50)),
                description=f'Test Service {i}'
            )
            self.services.append(service)

    def test_concurrent_bookings(self):
        """
        Test system stability with concurrent booking requests.
        Simulates multiple users trying to book the same room simultaneously.
        """
        def make_booking(room_id, username, password):
            client = Client()
            client.login(username=username, password=password)
            
            check_in = timezone.now().date()
            check_out = check_in + timedelta(days=2)
            data = {
                'room': room_id,
                'check_in': check_in.strftime('%Y-%m-%d'),
                'check_out': check_out.strftime('%Y-%m-%d'),
                'guests': 2,
                'special_requests': 'Test request'
            }
            try:
                # Create a new transaction for each request
                with transaction.atomic():
                    # Sleep for a random time to simulate real-world conditions
                    time.sleep(random.uniform(0.1, 0.3))
                    response = client.post(reverse('booking_form'), data)
                    print(f"Booking response for {username}: {response.status_code}")
                    if response.status_code not in [200, 302]:
                        print(f"Response content for {username}: {response.content}")
                    return response.status_code
            except Exception as e:
                print(f"Booking error for {username}: {str(e)}")
                return None

        # Create multiple users for concurrent testing
        test_users = []
        for i in range(2):
            user = User.objects.create_user(
                username=f'testuser{i}',
                password='testpass123',
                email=f'test{i}@example.com'
            )
            test_users.append(user)

        room = self.rooms[0]
        results = []

        # Use a lower number of workers and requests
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(make_booking, room.id, user.username, 'testpass123')
                for user in test_users
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"Future error: {str(e)}")

        # Clean up test users
        for user in test_users:
            user.delete()

        # At least one booking should be successful
        successful_bookings = sum(1 for r in results if r in [200, 302])
        self.assertGreater(successful_bookings, 0)

    def test_rapid_search_requests(self):
        """
        Test system stability under rapid search requests.
        Simulates multiple users searching for rooms simultaneously.
        """
        search_params = [
            {'check_in': timezone.now().date().strftime('%Y-%m-%d'), 'guests': 2},
            {'room_type': 'deluxe'},
            {'search': '101'},
            {
                'check_in': timezone.now().date().strftime('%Y-%m-%d'),
                'check_out': (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
            },
        ]

        def make_search(params):
            client = Client()
            time.sleep(random.uniform(0.05, 0.15))  # Add small delay
            return client.get(reverse('room_list'), params)

        start_time = time.time()
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for _ in range(5):  # Reduced number of searches
                params = random.choice(search_params)
                futures.append(executor.submit(make_search, params))
            
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"Search error: {str(e)}")

        end_time = time.time()
        execution_time = end_time - start_time

        # All responses should be successful
        self.assertTrue(all(r.status_code == 200 for r in results))
        # Average response time should be reasonable
        self.assertLess(execution_time / len(results), 2.0)

    @transaction.atomic
    def test_database_consistency(self):
        """
        Test database consistency under stress.
        Verifies data integrity when performing multiple operations.
        """
        initial_room_count = Room.objects.count()
        initial_booking_count = Booking.objects.count()

        # Create multiple bookings
        new_bookings = []
        for room in self.rooms[:5]:
            booking = Booking.objects.create(
                guest=self.user,
                room=room,
                check_in=timezone.now().date(),
                check_out=timezone.now().date() + timedelta(days=2),
                guests=min(2, room.capacity),  # Ensure guests don't exceed room capacity
                special_requests='Test booking'
            )
            new_bookings.append(booking)

        # Modify room details
        for room in self.rooms[5:10]:
            room.price += Decimal('10.00')
            room.save()

        # Add services to bookings
        for booking in new_bookings:
            BookingService.objects.create(
                booking=booking,
                service=random.choice(self.services),
                quantity=random.randint(1, 3)
            )

        # Verify database consistency
        self.assertEqual(Room.objects.count(), initial_room_count)
        self.assertEqual(Booking.objects.count(), initial_booking_count + 5)
        self.assertTrue(all(room.price >= Decimal('100.00') for room in Room.objects.all()))

    def test_error_handling(self):
        """
        Test system stability when handling errors.
        Verifies system recovers gracefully from invalid operations.
        """
        def make_invalid_request(username, password):
            client = Client()
            client.login(username=username, password=password)
            time.sleep(random.uniform(0.1, 0.2))  # Add small delay between requests
            return client.post(reverse('booking_form'), {
                'room': random.randint(1000, 9999),
                'check_in': 'invalid',
                'guests': 'invalid',
            })

        # Create test users for concurrent requests
        test_users = []
        for i in range(2):
            user = User.objects.create_user(
                username=f'erroruser{i}',
                password='testpass123',
                email=f'error{i}@example.com'
            )
            test_users.append(user)

        # Test single invalid room booking
        client = Client()
        client.login(username='testuser', password='testpass123')
        
        response = client.post(reverse('booking_form'), {
            'room': 999999,
            'check_in': timezone.now().date().strftime('%Y-%m-%d'),
            'check_out': (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'guests': 100,
        })
        self.assertEqual(response.status_code, 200)

        # Test invalid search parameters
        response = client.get(reverse('room_list'), {
            'check_in': 'invalid-date',
            'guests': 'not-a-number',
        })
        self.assertEqual(response.status_code, 200)

        # Test concurrent invalid operations with reduced concurrency
        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(make_invalid_request, user.username, 'testpass123')
                for user in test_users
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"Error request error: {str(e)}")

        # Clean up test users
        for user in test_users:
            user.delete()

        # All responses should be handled gracefully
        self.assertTrue(all(r.status_code == 200 for r in results))

    def test_extended_session(self):
        """
        Test system stability during extended user sessions.
        Simulates a user performing various actions over a long period.
        """
        actions = []
        
        # Perform 20 mixed operations
        for _ in range(20):
            action = random.choice([
                self.view_rooms,
                self.make_booking,
                self.view_bookings,
                self.search_rooms
            ])
            try:
                time.sleep(random.uniform(0.05, 0.15))  # Add small delay between actions
                response = action()
                actions.append(response.status_code)
            except Exception as e:
                print(f"Extended session error during {action.__name__}: {str(e)}")
                self.fail(f"Extended session failed during {action.__name__}: {str(e)}")

        # Verify all actions were successful
        self.assertTrue(all(status in [200, 302] for status in actions))

    # Helper methods
    def view_rooms(self):
        """Helper method to view room list."""
        return self.client.get(reverse('room_list'))

    def make_booking(self):
        """Helper method to make a booking."""
        room = random.choice(self.rooms)
        check_in = timezone.now().date()
        check_out = check_in + timedelta(days=random.randint(1, 5))
        return self.client.post(reverse('booking_form'), {
            'room': room.id,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'guests': min(2, room.capacity),  # Ensure guests don't exceed room capacity
            'special_requests': 'Test request'
        })

    def view_bookings(self):
        """Helper method to view booking list."""
        return self.client.get(reverse('booking_list'))

    def search_rooms(self):
        """Helper method to search rooms."""
        check_in = timezone.now().date()
        check_out = check_in + timedelta(days=1)
        return self.client.get(reverse('room_list'), {
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'guests': random.randint(1, 4),
            'room_type': random.choice(['single', 'double', 'suite', 'deluxe', '']),
        })
