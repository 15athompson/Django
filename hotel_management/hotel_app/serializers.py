from rest_framework import serializers
from .models import Room, Guest, Booking, Payment, Service, BookingService, Staff

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'number', 'room_type', 'capacity', 'price', 'description', 'is_available']

class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'room', 'check_in', 'check_out', 'guests', 'special_requests', 'created_at']
        read_only_fields = ['created_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class BookingServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingService
        fields = '__all__'

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'