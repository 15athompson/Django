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
