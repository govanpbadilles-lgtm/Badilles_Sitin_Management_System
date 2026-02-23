document.addEventListener('DOMContentLoaded', function() {
    
    const loginModal = document.getElementById("loginModal");

    if (loginModal) {
        const loginBtn = document.getElementById("loginLink");
        const closeBtn = document.querySelector(".close-btn"); 

        if (loginBtn) {
            loginBtn.addEventListener('click', function(event) {
                event.preventDefault();       
                loginModal.style.display = "flex"; 
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                loginModal.style.display = "none"; 
            });
        }

        window.addEventListener('click', function(event) {
            if (event.target === loginModal) {
                loginModal.style.display = "none";
            }
        });

        // --- AUTO-OPEN MODAL & SHOW TOASTS ---
        const urlParams = new URLSearchParams(window.location.search);
        
        // 1. If coming from the normal "Login" link on register page
        if (urlParams.get('openLogin') === 'true') {
            loginModal.style.display = "flex";
        }
        
        // 2. If coming from a SUCCESSFUL registration
        if (urlParams.get('registered') === 'true') {
            // Wait just a tiny bit (100ms) for the page to render, then show toast
            setTimeout(() => {
                showToast('success', 'Registration successful');
            }, 100);
            
            // Open the login modal automatically
            loginModal.style.display = "flex";
            
            // Clean up the URL so the toast doesn't pop up again if they refresh the page
            window.history.replaceState({}, document.title, "/"); 
        }
    }

    const regForm = document.getElementById('regForm');

    if (regForm) {
        
        regForm.addEventListener('submit', function(event) {
            
            const pass1 = document.getElementById('password').value;
            const pass2 = document.getElementById('confirm_password').value;
            
            if (pass1 !== pass2) {
                event.preventDefault(); 
                alert("Passwords do not match! Please try again."); 
            }
        });
    }

});

// =======================================================
// TOAST NOTIFICATION LOGIC
// =======================================================

function showToast(type, message) {
    let toastBox = document.getElementById('toastBox');
    
    // Safety check just in case the HTML div is missing
    if (!toastBox) return; 

    let toast = document.createElement('div');
    
    // Add the base class and the type class (success or error)
    toast.classList.add('toast');
    toast.classList.add(type);

    // Set the icon based on the type
    let icon = '';
    if (type === 'success') {
        icon = '<i class="fas fa-check-circle"></i>';
    } else if (type === 'error') {
        icon = '<i class="fas fa-times-circle"></i>';
    }

    // Insert the icon and message into the div
    toast.innerHTML = icon + message;
    
    // Add the toast to the screen
    toastBox.appendChild(toast);

    // Remove the toast automatically after 3.5 seconds
    setTimeout(() => {
        toast.remove();
    }, 3500);
}