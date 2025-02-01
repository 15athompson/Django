from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Room(models.Model):
    number = models.CharField(max_length=10)
    room_type = models.CharField(max_length=50)
    capacity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.number} - {self.room_type}"

    def save(self, *args, **kwargs):
        if self.pk is None and Room.objects.filter(number=self.number).exists():
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Room with number {self.number} already exists.")
        super().save(*args, **kwargs)

class Guest(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)

class Booking(models.Model):
    guest = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField()
    special_requests = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)  # This line is now correct

    def __str__(self):
        return f"Booking {self.id} - Room {self.room.number} for {self.guests} guests"

class Payment(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=[
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('cash', 'Cash'),
        ('paypal', 'PayPal'),
    ])
    transaction_id = models.CharField(max_length=100, unique=True)

class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()

class BookingService(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

class Staff(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=50, choices=[
        ('manager', 'Manager'),
        ('housekeeping', 'Housekeeping'),
        ('reception', 'Reception'),
        ('maintenance', 'Maintenance'),
    ])
