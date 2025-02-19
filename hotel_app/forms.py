from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'check_in_date', 'check_out_date', 'guest_name', 'guest_email']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        room = cleaned_data.get('room')

        if check_in_date and check_out_date and room:
            # Validate check-in date is not in the past
            if check_in_date < datetime.now().date():
                raise ValidationError("Check-in date cannot be in the past.")

            # Validate check-out date is after check-in date
            if check_out_date <= check_in_date:
                raise ValidationError("Check-out date must be after check-in date.")

            # Validate maximum stay duration (e.g., 30 days)
            max_stay = 30
            if (check_out_date - check_in_date).days > max_stay:
                raise ValidationError(f"Maximum stay duration is {max_stay} days.")

            # Validate minimum stay duration (e.g., 1 night)
            min_stay = 1
            if (check_out_date - check_in_date).days < min_stay:
                raise ValidationError(f"Minimum stay duration is {min_stay} night.")

            # Validate advance booking (e.g., maximum 6 months ahead)
            max_advance = datetime.now().date() + timedelta(days=180)
            if check_in_date > max_advance:
                raise ValidationError("Bookings can only be made up to 6 months in advance.")

            # Check for overlapping bookings
            overlapping_bookings = Booking.objects.filter(
                room=room,
                check_out_date__gt=check_in_date,
                check_in_date__lt=check_out_date
            )

            # Exclude current booking when editing
            if self.instance.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.instance.pk)

            if overlapping_bookings.exists():
                raise ValidationError("This room is already booked for the selected dates.")

        return cleaned_data