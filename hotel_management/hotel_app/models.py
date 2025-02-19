from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError

class Role(models.Model):
    """Represents a role within the system."""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name if self.role else 'No Role'}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class Room(models.Model):
    """Represents a hotel room with its properties and availability status."""
    ROOM_TYPES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
        ('deluxe', 'Deluxe'),
    ]

    number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=50, choices=ROOM_TYPES)
    capacity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Room {self.number} - {self.room_type}"

    def save(self, *args, **kwargs):
        """Override save method to ensure room number uniqueness."""
        if self.pk is None and Room.objects.filter(number=self.number).exists():
            raise ValidationError(f"Room with number {self.number} already exists.")
        super().save(*args, **kwargs)

    def is_available_for_dates(self, check_in, check_out):
        """Check if the room is available for the given date range."""
        from django.db.models import Q
        overlapping_bookings = self.booking_set.filter(
            Q(check_in__lte=check_out) & Q(check_out__gte=check_in)
        ).exists()
        return not overlapping_bookings

    def get_next_available_date(self):
        """Get the next available date for booking the room."""
        today = timezone.now().date()
        bookings = self.booking_set.filter(check_out__gte=today).order_by('check_out')
        if not bookings:
            return today
        return bookings.last().check_out

class Booking(models.Model):
    """Represents a room booking with guest information and stay duration."""
    guest = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField()
    special_requests = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        """Validate the booking data before saving."""
        if self.check_in and self.check_out:
            if self.check_in >= self.check_out:
                raise ValidationError("Check-out date must be after check-in date")
            if self.check_in < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past")
            if not self.room.is_available_for_dates(self.check_in, self.check_out):
                raise ValidationError("Room is not available for these dates")
            if self.guests > self.room.capacity:
                raise ValidationError(f"Number of guests exceeds room capacity of {self.room.capacity}")

    def save(self, *args, **kwargs):
        """Override save method to ensure validation is performed before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} - Room {self.room.number} for {self.guests} guests"

    def get_total_price(self):
        """Calculate total price for the booking including room and additional services."""
        from datetime import datetime
        nights = (self.check_out - self.check_in).days
        room_total = self.room.price * nights
        service_total = sum(bs.service.price * bs.quantity for bs in self.bookingservice_set.all())
        return room_total + service_total

class Guest(models.Model):
    """Represents a hotel guest's personal information."""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Payment(models.Model):
    """Represents a payment transaction for a booking."""
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('cash', 'Cash'),
        ('paypal', 'PayPal'),
    ]

    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Booking {self.booking.id}"

class Service(models.Model):
    """Represents additional services offered by the hotel."""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return f"{self.name} (${self.price})"

class BookingService(models.Model):
    """Represents services booked as part of a room booking."""
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.service.name} x{self.quantity} for Booking {self.booking.id}"

class Staff(models.Model):
    """Represents hotel staff members and their roles."""
    STAFF_ROLES = [
        ('manager', 'Manager'),
        ('housekeeping', 'Housekeeping'),
        ('reception', 'Reception'),
        ('maintenance', 'Maintenance'),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=50, choices=STAFF_ROLES)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_role_display()}"
