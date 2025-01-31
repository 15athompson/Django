from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.contrib.auth import views as auth_views

from django.urls import reverse

class CustomLogoutView(auth_views.LogoutView):
    next_page = 'logout_success'  # Redirect to the logout success page

    def get_next_page(self):
        return reverse('logout_success')


# Create a router for RESTful API endpoints
router = DefaultRouter()
router.register(r'rooms', views.RoomViewSet, basename='room')
router.register(r'guests', views.GuestViewSet, basename='guest')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'bookingservices', views.BookingServiceViewSet, basename='bookingservice')
router.register(r'staff', views.StaffViewSet, basename='staff')

# URL patterns for the application
urlpatterns = [
    # API endpoints (under 'api/' namespace)
    path('api/', include((router.urls, 'api'), namespace='api')),

    # Traditional Django views
    path('', views.home, name='home'),  # Home page
    path('rooms/', views.room_list, name='room_list'),  # Room list view
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),  # Room detail view
    path('booking/', views.booking_form, name='booking_form'),  # Booking form view
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),  # Booking confirmation view
    path('bookings/', views.booking_list, name='booking_list'),  # Booking list view
    path('login/', auth_views.LoginView.as_view(template_name='hotel_app/login.html'), name='login'),  # Login view
    path('logout/', CustomLogoutView.as_view(), name='logout'),  # Use the custom logout view
    path('logout/success/', views.logout_success, name='logout_success'),  # Optional: Redirect to a success page
]
