import time
import requests
import threading
from django.test import TestCase

# Define the target URL
url = "http://localhost:8000/api/rooms/"  # Replace with your actual URL

# Define the number of requests to send
num_requests = 100

# Define a function to send a request
def send_request():
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Request successful")
        else:
            print(f"Request failed with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed with exception: {e}")


class StressTest(TestCase):
    def test_stress(self):
        # Create a list of threads
        threads = []
        for i in range(num_requests):
            thread = threading.Thread(target=send_request)
            threads.append(thread)

        # Start the threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        end_time = time.time()

        print(f"Total time taken: {end_time - start_time} seconds")
        print("Stress test complete!")
