// =======================================================
// STUDENT DASHBOARD JAVASCRIPT
// =======================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // Check para sa Login Success Toast
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('login') === 'success') {
        setTimeout(() => {
            if (typeof showToast === 'function') {
                showToast('success', 'Logged in successfully!');
            }
        }, 100);
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // Check para sa Update Profile Success Toast
    if (urlParams.get('update') === 'success') {
        setTimeout(() => {
            if (typeof showToast === 'function') {
                showToast('success', 'Profile updated successfully!');
            }
        }, 100);
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // =======================================================
    // EDIT PROFILE MODAL LOGIC (GIKAN SA NAVBAR)
    // =======================================================
    const openEditProfileBtn = document.getElementById('openEditProfileBtn');
    const editProfileModal = document.getElementById('editProfileModal');
    const closeEditProfileBtn = document.getElementById('closeEditProfileBtn');

    if (openEditProfileBtn) {
        openEditProfileBtn.addEventListener('click', (e) => {
            e.preventDefault(); // Pugngan nga mo-scroll pataas ang screen
            editProfileModal.style.display = 'flex';
        });
    }

    if (closeEditProfileBtn) {
        closeEditProfileBtn.addEventListener('click', () => {
            editProfileModal.style.display = 'none';
        });
    }

    // Isira ang modal kung mo-click sa gawas
    window.addEventListener('click', function(e) {
        if (e.target === editProfileModal) {
            editProfileModal.style.display = 'none';
        }
    });

});