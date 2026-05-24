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
// GLOBAL NOTIFICATIONS SYSTEM
// =======================================================
(function() {
    const fetchCount = () => {
        const badge = document.getElementById('notifBadge');
        if (!badge) return;
        fetch('/notifications/count')
            .then(r => r.json())
            .then(data => {
                badge.style.display = data.count > 0 ? 'flex' : 'none';
                badge.textContent = data.count;
            })
            .catch(err => console.error("Notif Error:", err));
    };
    
    // Initial fetch if badge exists
    if (document.getElementById('notifBadge')) {
        fetchCount();
        setInterval(fetchCount, 30000);
    }
})();

function toggleNotifDropdown(e) {
    if (e) e.stopPropagation();
    const dd = document.getElementById('notifDropdown');
    if (!dd) return;
    
    const isOpen = dd.style.display === 'block';
    dd.style.display = isOpen ? 'none' : 'block';
    
    if (!isOpen) loadNotifications();
}

function loadNotifications() {
    const list = document.getElementById('notifList');
    if (!list) return;
    
    list.innerHTML = '<div class="notif-empty"><p><i class="fas fa-spinner fa-spin"></i> Loading...</p></div>';
    
    fetch('/notifications/list')
        .then(r => r.json())
        .then(items => {
            if (!items.length) {
                list.innerHTML = '<div class="notif-empty"><i class="fas fa-bell-slash"></i><p>No notifications yet</p></div>';
                return;
            }
            
            list.innerHTML = '';
            items.forEach(item => {
                const div = document.createElement('a');
                div.href = item.link || '#';
                div.className = 'notif-item' + (item.is_read ? '' : ' unread');
                
                let iconClass = 'fa-bell';
                if (item.type === 'reservation') iconClass = 'fa-calendar-check';
                else if (item.type === 'approved') iconClass = 'fa-check-circle';
                else if (item.type === 'declined') iconClass = 'fa-times-circle';
                else if (item.type === 'announcement') iconClass = 'fa-bullhorn';

                div.innerHTML = `
                    <div class="notif-icon ${item.type || ''}">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="notif-body">
                        <p class="notif-msg">${item.message}</p>
                        <span class="notif-time">${item.created_at || ''}</span>
                    </div>
                    ${!item.is_read ? '<div class="notif-unread-dot"></div>' : ''}
                `;
                
                div.onclick = (e) => {
                    if (item.link) e.preventDefault();
                    fetch('/notifications/read/' + item.id, { method: 'POST' })
                        .then(() => {
                            if (item.link) window.location.href = item.link;
                            else loadNotifications();
                        });
                };
                list.appendChild(div);
            });
        })
        .catch(err => {
            list.innerHTML = '<div class="notif-empty"><p>Error loading notifications</p></div>';
        });
}

function markAllRead() {
    fetch('/notifications/read_all', { method: 'POST' })
        .then(() => {
            loadNotifications();
            const badge = document.getElementById('notifBadge');
            if (badge) badge.style.display = 'none';
        });
}

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    const dd = document.getElementById('notifDropdown');
    if (dd) dd.style.display = 'none';
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