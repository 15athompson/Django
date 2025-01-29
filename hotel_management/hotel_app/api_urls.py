from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, BookingViewSet

router = DefaultRouter()
router.register('rooms', RoomViewSet, basename='room')
router.register('bookings', BookingViewSet, basename='booking')

urlpatterns = router.urls
