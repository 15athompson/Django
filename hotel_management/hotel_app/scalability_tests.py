from locust import HttpUser, task, between

class HotelUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://localhost:8000"

    @task
    def view_rooms(self):
        self.client.get("/rooms/")
