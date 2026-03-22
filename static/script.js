document.addEventListener('DOMContentLoaded', function() {
    
    const loginModal = document.getElementById("loginModal");

    if (loginModal) {
        // GI-FIX: Gi-ilisag "openLogin" aron mo-match sa imong HTML
        const loginBtn = document.getElementById("openLogin"); 
        
        // GI-DUGANG: Apilon nato ang "Get Started" button
        const getStartedBtn = document.getElementById("getStartedBtn"); 
        
        const closeBtn = document.querySelector(".close-btn"); 

        // Inig click sa Login button sa Navbar
        if (loginBtn) {
            loginBtn.addEventListener('click', function(event) {
                event.preventDefault();       
                loginModal.style.display = "flex"; 
            });
        }

        // Inig click sa "Get Started" button sa tunga
        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', function(event) {
                event.preventDefault();       
                loginModal.style.display = "flex"; 
            });
        }

        // Inig click sa "X" button
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                loginModal.style.display = "none"; 
            });
        }

        // Inig click sa gawas sa puti nga kahon
        window.addEventListener('click', function(event) {
            if (event.target === loginModal) {
                loginModal.style.display = "none";
            }
        });

        // --- AUTO-OPEN MODAL & SHOW TOASTS ---
        const urlParams = new URLSearchParams(window.location.search);
        
        if (urlParams.get('openLogin') === 'true') {
            loginModal.style.display = "flex";
        }
        
        if (urlParams.get('registered') === 'true') {
            setTimeout(() => {
                showToast('success', 'Registration successful! You can now login.');
            }, 100);
            loginModal.style.display = "flex";
            window.history.replaceState({}, document.title, "/"); 
        }

        // --- FAILED LOGIN ---
        if (urlParams.get('error') === 'true') {
            setTimeout(() => {
                // GI-FIX: Gi-ilisag "ID Number" ang text
                showToast('error', 'Incorrect ID Number or password!');
            }, 100);
            loginModal.style.display = "flex";
            window.history.replaceState({}, document.title, "/"); 
        }
    }

    // Password matching logic para sa Registration
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