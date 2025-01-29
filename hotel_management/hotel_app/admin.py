from django.contrib import admin
from .models import Room, Guest, Booking, Payment, Service, BookingService, Staff

admin.site.register(Room)
admin.site.register(Guest)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Service)
admin.site.register(BookingService)
admin.site.register(Staff)