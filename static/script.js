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
            setTimeout(() => {
                showToast('success', 'Registration successful');
            }, 100);
            loginModal.style.display = "flex";
            window.history.replaceState({}, document.title, "/"); 
        }

        // 3. --- NEW: If coming from a FAILED login ---
        if (urlParams.get('error') === 'true') {
            setTimeout(() => {
                showToast('error', 'Incorrect email or password!');
            }, 100);
            loginModal.style.display = "flex";
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
    
    if (!toastBox) return; 

    let toast = document.createElement('div');
    
    toast.classList.add('toast');
    toast.classList.add(type);

    let icon = '';
    if (type === 'success') {
        icon = '<i class="fas fa-check-circle"></i>';
    } else if (type === 'error') {
        icon = '<i class="fas fa-times-circle"></i>';
    }

    toast.innerHTML = icon + message;
    toastBox.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3500);
}