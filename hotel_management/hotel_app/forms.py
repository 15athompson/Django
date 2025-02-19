from django import forms
from django.utils import timezone
from .models import Booking, Room

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'check_in', 'check_out', 'guests', 'special_requests']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
            'special_requests': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        guests = cleaned_data.get('guests')

        if check_in and check_out and check_in >= check_out:
            raise forms.ValidationError("Check-out date must be after check-in date")

        # print(timezone.now().date())
        # print(check_in)

        # if check_in and check_in < timezone.now().date():
        #     raise forms.ValidationError({'check_in': "Check-in date cannot be in the past"})

        if room and check_in and check_out:
            overlapping_bookings = Booking.objects.filter(
                room=room,
                check_in__lt=check_out,
                check_out__gt=check_in,
            )
            if overlapping_bookings.exists():
                raise forms.ValidationError(
                    "This room is already booked for the selected dates."
                )

        return cleaned_data
