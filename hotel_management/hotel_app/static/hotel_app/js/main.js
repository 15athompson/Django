// main.js

document.addEventListener('DOMContentLoaded', function () {
    // Function to handle form submission for booking
    const bookingForm = document.querySelector('#bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent default form submission

            // Validate form fields
            const checkIn = document.querySelector('input[name="check_in"]').value;
            const checkOut = document.querySelector('input[name="check_out"]').value;
            const guests = document.querySelector('input[name="guests"]').value;

            if (!checkIn || !checkOut || !guests) {
                alert('Please fill in all required fields.');
                return;
            }

            // If validation passes, submit the form via AJAX
            const formData = new FormData(bookingForm);
            fetch(bookingForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken') // Include CSRF token for security
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json(); // Assuming the server responds with JSON
                }
                throw new Error('Network response was not ok.');
            })
            .then(data => {
                // Redirect to confirmation page or show success message
                window.location.href = `/booking/confirmation/${data.booking_id}/`;
            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
        });
    }

    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Check if this cookie string begins with the name we want
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Example: Handle logout confirmation
    const logoutForm = document.querySelector('#logoutForm');
    if (logoutForm) {
        logoutForm.addEventListener('submit', function (event) {
            const confirmation = confirm('Are you sure you want to log out?');
            if (!confirmation) {
                event.preventDefault(); // Prevent logout if user cancels
            }
        });
    }
});