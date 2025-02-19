from django.test import TestCase, Client
from django.urls import reverse
import time
import random

class LoadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.urls = [
            reverse('home'),
            reverse('room-list'),
            reverse('booking-list'),
            # Add more URLs as needed
        ]
        
    def test_multiple_requests(self):
        """Test handling multiple simultaneous requests"""
        start_time = time.time()
        num_requests = 100  # Number of requests to simulate
        successful_requests = 0
        
        for _ in range(num_requests):
            url = random.choice(self.urls)
            response = self.client.get(url)
            if response.status_code == 200:
                successful_requests += 1
                
        end_time = time.time()
        total_time = end_time - start_time
        
        # Assert that all requests were successful
        self.assertEqual(successful_requests, num_requests)
        
        # Log performance metrics
        print(f"\nLoad Test Results:")
        print(f"Total Requests: {num_requests}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Requests per Second: {num_requests/total_time:.2f}")
        
    def test_concurrent_users(self):
        """Test handling concurrent users"""
        # This would require a more sophisticated approach using threading
        # or a dedicated load testing tool
        pass
        
    def test_endurance(self):
        """Test system stability under sustained load"""
        # This would involve running tests over an extended period
        pass
