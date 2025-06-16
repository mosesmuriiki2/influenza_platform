// Form validation for registration forms
document.addEventListener('DOMContentLoaded', function() {
    // Get all registration forms
    const registrationForms = document.querySelectorAll('form');
    
    registrationForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Get password fields if they exist
            const passwordField = form.querySelector('#id_password');
            const confirmPasswordField = form.querySelector('#id_confirm_password');
            const emailField = form.querySelector('#id_email');
            
            let isValid = true;
            let errorMessage = '';
            
            // Check if email exists and validate format
            if (emailField) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(emailField.value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid email address.';
                    showToast('error', errorMessage);
                }
            }
            
            // Check if password fields exist and validate
            if (passwordField && confirmPasswordField) {
                // Check if passwords match
                if (passwordField.value !== confirmPasswordField.value) {
                    isValid = false;
                    errorMessage = 'Passwords do not match.';
                    showToast('error', errorMessage);
                }
                
                // Check password length
                if (passwordField.value.length < 8) {
                    isValid = false;
                    errorMessage = 'Password must be at least 8 characters long.';
                    showToast('error', errorMessage);
                }
            }
            
            // If validation fails, prevent form submission
            if (!isValid) {
                event.preventDefault();
            }
        });
    });
    
    // Function to show toast notifications
    function showToast(type, message) {
        const toastContainer = document.querySelector('.toast-container');
        
        if (!toastContainer) return;
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'toast show animate__animated animate__fadeInRight';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // Set header background based on message type
        let bgClass = 'bg-info';
        let icon = 'bi-info-circle';
        let title = 'Information';
        
        if (type === 'success') {
            bgClass = 'bg-success';
            icon = 'bi-check-circle';
            title = 'Success';
        } else if (type === 'error') {
            bgClass = 'bg-danger';
            icon = 'bi-exclamation-triangle';
            title = 'Error';
        } else if (type === 'warning') {
            bgClass = 'bg-warning';
            icon = 'bi-exclamation-circle';
            title = 'Warning';
        }
        
        // Create toast content
        toast.innerHTML = `
            <div class="toast-header ${bgClass} text-white">
                <i class="bi ${icon} me-2"></i>
                <strong class="me-auto">${title}</strong>
                <small>Just now</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Add toast to container
        toastContainer.appendChild(toast);
        
        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000 // Auto-hide after 5 seconds
        });
        
        // Remove toast from DOM after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
});