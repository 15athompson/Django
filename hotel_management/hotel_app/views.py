from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsStaff, IsManager, IsReceptionist, IsHousekeeping, IsMaintenance
from .models import Room, Guest, Booking, Payment, Service, BookingService, Staff
from .serializers import (
    RoomSerializer, GuestSerializer, BookingSerializer,
    PaymentSerializer, ServiceSerializer, BookingServiceSerializer,
    StaffSerializer
)
from .forms import BookingForm
from django.core.exceptions import ValidationError

class GuestViewSet(viewsets.ModelViewSet):
    permission_classes = []
    """ViewSet for viewing and editing guest information."""
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer


class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = []
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if Room.objects.filter(number=serializer.validated_data['number']).exists():
            return Response(
                {"error": "Room with this number already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = []
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check room availability
        room = get_object_or_404(Room, id=serializer.validated_data['room'].id)
        check_in = serializer.validated_data['check_in']
        check_out = serializer.validated_data['check_out']

        if not room.is_available_for_dates(check_in, check_out):
            return Response(
                {"error": "Room is not available for these dates"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.validated_data['guests'] > room.capacity:
            return Response(
                {"error": f"Number of guests exceeds room capacity of {room.capacity}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

def home(request):
    available_rooms = Room.objects.filter(is_available=True)
    return render(request, 'hotel_app/home.html', {'rooms': available_rooms})

def room_list(request):
    today = timezone.now().date()
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    guests = request.GET.get('guests')
    room_type = request.GET.get('room_type')
    search_query = request.GET.get('search', '').strip()  # Add search query parameter

    rooms = Room.objects.all()

    # Search by room number or room type
    if search_query:
        # Try to convert search query to integer for room number search
        try:
            room_number = int(search_query)
            rooms = rooms.filter(number=room_number)
        except ValueError:
            # If not a number, search by room type (case-insensitive partial match)
            rooms = rooms.filter(
                Q(room_type__icontains=search_query) |
                Q(description__icontains=search_query)
            )

    # Filter by availability if dates are provided
    if check_in and check_out:
        try:
            check_in = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()

            # Exclude rooms with overlapping bookings
            unavailable_rooms = Room.objects.filter(
                booking__check_in__lt=check_out,
                booking__check_out__gt=check_in
            ).distinct()

            rooms = rooms.exclude(id__in=unavailable_rooms)
        except ValueError:
            messages.error(request, "Invalid date format")

    # Filter by number of guests
    if guests:
        try:
            rooms = rooms.filter(capacity__gte=int(guests))
        except ValueError:
            messages.error(request, "Invalid number of guests")

    # Filter by room type
    if room_type:
        rooms = rooms.filter(room_type=room_type)

    context = {
        'rooms': rooms,
        'room_types': Room.ROOM_TYPES,
        'check_in': check_in,
        'check_out': check_out,
        'guests': guests,
        'room_type': room_type,
        'search_query': search_query,  # Add search query to context
        'today': today,  # Add today's date to context
    }

    return render(request, 'hotel_app/room_list.html', context)

def room_detail(request, pk):
    """
    Retrieve and display details of a specific room, including upcoming bookings and the next available date.
    """
    room = get_object_or_404(Room, pk=pk)
    # Get upcoming bookings for availability calendar
    upcoming_bookings = room.booking_set.filter(
        check_out__gte=timezone.now().date()
    ).order_by('check_in')

    context = {
        'room': room,
        'upcoming_bookings': upcoming_bookings,
        'next_available': room.get_next_available_date()
    }
    return render(request, 'hotel_app/room_detail.html', context)

@login_required
def booking_form(request):
    """
    
    
        This view handles both GET and POST requests. On GET, it displays the booking form with optional initial data for room, check-in, and check-out dates. On POST, it validates and processes the booking form, saving the booking if valid, and redirects to a confirmation page.
    """
    room_id = request.GET.get('room_id')
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    if room_id:
        room = get_object_or_404(Room, id=room_id)
        initial_data = {'room': room}

        if check_in and check_out:
            initial_data.update({
                'check_in': check_in,
                'check_out': check_out
            })
    else:
        room = None
        initial_data = {}

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            if room:
                booking.room = room
            booking.guest = request.user

            try:
                booking.clean()  # Run model validation
                booking.save()
                messages.success(request, 'Booking successful!')
                return redirect('booking_confirmation', booking_id=booking.id)
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = BookingForm(initial=initial_data)

    context = {
        'form': form,
        'room': room,
        'available_rooms': Room.objects.filter(is_available=True)
    }
    return render(request, 'hotel_app/booking_form.html', context)

@login_required
def booking_list(request):
    bookings = Booking.objects.filter(guest=request.user).order_by('-created_at')
    return render(request, 'hotel_app/booking_list.html', {'bookings': bookings})

@login_required
def create_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.guest = request.user
            booking.save()
            messages.success(request, 'Booking created successfully.')
            return redirect('booking_list')
    else:
        form = BookingForm()
    return render(request, 'hotel_app/booking_form.html', {'form': form})

@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Booking updated successfully.')
            return redirect('booking_list')
        else:
            print(form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'hotel_app/booking_edit.html', {'form': form, 'booking': booking})

@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Booking deleted successfully.')
        return redirect('booking_list')
    return render(request, 'hotel_app/booking_confirm_delete.html', {'booking': booking})

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    total_price = booking.get_total_price()
    return render(request, 'hotel_app/booking_confirmation.html', {
        'booking': booking,
        'total_price': total_price
    })

def logout_success(request):
    return render(request, 'hotel_app/logout.html')

class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = []
    """ViewSet for viewing and editing payment information."""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    permission_classes = []
    """ViewSet for viewing and editing hotel services."""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class BookingServiceViewSet(viewsets.ModelViewSet):
    permission_classes = []
    """ViewSet for viewing and editing booking services."""
    queryset = BookingService.objects.all()
    serializer_class = BookingServiceSerializer


class StaffViewSet(viewsets.ModelViewSet):
    permission_classes = []
    """ViewSet for viewing and editing staff information. Only accessible by staff members."""
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    def get_queryset(self):
        """Only staff members can view staff information"""
        user = self.request.user
        if user.is_staff:
            return Staff.objects.all()
        return Staff.objects.none()
