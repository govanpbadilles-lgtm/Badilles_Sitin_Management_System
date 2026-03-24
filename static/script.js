// =======================================================
// GLOBAL SCRIPT & TOAST NOTIFICATIONS
// =======================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. GLOBAL URL CHECKER PARA SA MGA TOASTS NGA DILI MASABLAY
    const urlParams = new URLSearchParams(window.location.search);
    
    // -- Admin/Student Login Success --
    if (urlParams.get('login') === 'success') {
        setTimeout(() => showToast('success', 'Logged in successfully!'), 100);
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // -- Logout Success --
    if (urlParams.get('logout') === 'success') {
        setTimeout(() => showToast('success', 'Logged out successfully!'), 100);
        window.history.replaceState({}, document.title, window.location.pathname); 
    }

    // -- Failed Login --
    if (urlParams.get('error') === 'true') {
        setTimeout(() => showToast('error', 'Incorrect Email or password!'), 100);
        // Wala gi-clear ang URL diri aron ma-abli ang modal sa ubos
    }

    // -- Registration Success --
    if (urlParams.get('registered') === 'true') {
        setTimeout(() => showToast('success', 'Registration successful! You can now login.'), 100);
        // Wala gi-clear ang URL diri aron ma-abli ang modal sa ubos
    }

    // =======================================================
    // LOGIN MODAL LOGIC (PARA SA HOME PAGE)
    // =======================================================
    const loginModal = document.getElementById("loginModal");

    if (loginModal) {
        const loginBtn = document.getElementById("openLogin"); 
        const getStartedBtn = document.getElementById("getStartedBtn"); 
        const closeBtn = document.querySelector(".close-btn"); 

        // Open Modal Buttons
        if (loginBtn) {
            loginBtn.addEventListener('click', function(e) {
                e.preventDefault();       
                loginModal.style.display = "flex"; 
            });
        }

        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', function(e) {
                e.preventDefault();       
                loginModal.style.display = "flex"; 
            });
        }

        // Close Modal Logic
        if (closeBtn) {
            closeBtn.addEventListener('click', () => loginModal.style.display = "none");
        }

        window.addEventListener('click', function(event) {
            if (event.target === loginModal) loginModal.style.display = "none";
        });

        // AUTO-OPEN MODAL KUNG NAAY ERROR O BAG-ONG REGISTER
        if (urlParams.get('openLogin') === 'true' || urlParams.get('registered') === 'true' || urlParams.get('error') === 'true') {
            loginModal.style.display = "flex";
            // Karon pa nato i-clear ang URL aron limpyo
            window.history.replaceState({}, document.title, window.location.pathname); 
        }
    }

    // =======================================================
    // REGISTRATION FORM LOGIC (PASSWORD MATCHING)
    // =======================================================
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
// TOAST NOTIFICATION FUNCTION
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