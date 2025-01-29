from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Room, Guest, Booking, Payment, Service, BookingService, Staff
from .serializers import RoomSerializer, GuestSerializer, BookingSerializer, PaymentSerializer, ServiceSerializer, BookingServiceSerializer, StaffSerializer

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def create(self, request, *args, **kwargs):
        # Get room_id from request data or query parameters
        room_id = request.data.get('room') or request.query_params.get('room_id')
        if not room_id:
            return Response(
                {"error": "room_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add room_id to the request data
        data = request.data.copy()
        data['room'] = room_id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class BookingServiceViewSet(viewsets.ModelViewSet):
    queryset = BookingService.objects.all()
    serializer_class = BookingServiceSerializer

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Room, Booking

def home(request):
    return render(request, 'hotel_app/home.html')

def room_list(request):
    print("Room list view called")  # Debugging line
    rooms = Room.objects.filter(is_available=True)  # Only show available rooms
    print(f"Available rooms: {rooms}")  # Debugging line
    return render(request, 'hotel_app/room_list.html', {'rooms': rooms})

def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    return render(request, 'hotel_app/room_detail.html', {'room': room})

def booking_list(request):
       bookings = Booking.objects.all()  # Fetch all bookings
       return render(request, 'hotel_app/booking_list.html', {'bookings': bookings})

class RoomListView(ListView):
    model = Room
    template_name = 'hotel_app/room_list.html'
    context_object_name = 'rooms'

class RoomDetailView(DetailView):
    model = Room
    template_name = 'hotel_app/room_detail.html'
    context_object_name = 'room'

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Room, Booking
from .forms import BookingForm


from django.contrib.auth.decorators import login_required





@login_required
def booking_form(request):
    room_id = request.GET.get('room_id')  # Get room_id from query parameters
    room = get_object_or_404(Room, id=room_id) if room_id else None  # Fetch the room or return 404

    if request.method == 'POST':
        form = BookingForm(request.POST)  # Bind form data to the form
        if form.is_valid():
            # Create a booking object but don't save it yet
            booking = form.save(commit=False)
            booking.room = room  # Assign the room to the booking
            booking.guest = request.user  # Assign the logged-in user as the guest
            booking.save()  # Save the booking to the database

            # Display a success message
            messages.success(request, 'Booking successful!')
            
            # Redirect to the booking confirmation page
            return redirect('booking_confirmation', booking_id=booking.id)
        else:
            # If the form is invalid, display error messages
            messages.error(request, 'Please correct the errors below.')
            print("Form errors:", form.errors)  # Print form errors to the console for debugging
    else:
        form = BookingForm()  # Display an empty form for GET requests

    # Render the booking form template with the form and room context
    return render(request, 'hotel_app/booking_form.html', {
        'form': form,
        'room': room
    })

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id) # Fetch the booking or return 404
    return render(request, 'hotel_app/booking_confirmation.html', {
        'booking': booking
    })