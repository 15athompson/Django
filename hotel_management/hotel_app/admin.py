from django.contrib import admin
from .models import Room, Guest, Booking, Payment, Service, BookingService, Staff
from django.core.exceptions import ValidationError
from django.contrib import messages

class RoomAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        try:
            if not Room.objects.filter(number=obj.number).exists() or obj.pk:
                super().save_model(request, obj, form, change)
        except ValidationError as e:
            messages.error(request, e)
        
        if Room.objects.filter(number=obj.number).exists() and not obj.pk:
            messages.error(request, f"Room with number {obj.number} already exists.")

admin.site.register(Room, RoomAdmin)
admin.site.register(Guest)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Service)
admin.site.register(BookingService)
admin.site.register(Staff)
