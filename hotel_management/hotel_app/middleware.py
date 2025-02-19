from django.shortcuts import redirect
from django.contrib import messages
import re

class DeletedBookingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the URL matches any of the booking detail patterns
        booking_patterns = [
            r'/bookings/edit/\d+/',
            r'/bookings/delete/\d+/',
            r'/booking/confirmation/\d+/'
        ]
        
        path = request.path
        if any(re.match(pattern, path) for pattern in booking_patterns):
            from .models import Booking
            booking_id = path.split('/')[-2]
            if not Booking.objects.filter(id=booking_id).exists():
                messages.error(request, 'The booking you were viewing no longer exists.')
                return redirect('booking_list')
                
        return self.get_response(request)
    

from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token
from django.http import HttpResponseRedirect

from django.urls import reverse

class AdminLogoutCSRFMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path in ['/admin/logout/', '/logout/'] and request.method == 'POST':
            csrf_token = get_token(request)
            if csrf_token:
                response = HttpResponseRedirect(reverse('logout_success'))
                response.set_cookie('csrftoken', csrf_token)
                return response
        return response
