// =======================================================
// STUDENT DASHBOARD JAVASCRIPT
// =======================================================

document.addEventListener('DOMContentLoaded', function() {

    // =======================================================
    // URL PARAMS - TOAST NOTIFICATIONS
    // =======================================================
    const urlParams = new URLSearchParams(window.location.search);

    // Check para sa Login Success Toast
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

    // Check para sa Feedback Success Toast
    if (urlParams.get('feedback') === 'success') {
        setTimeout(() => {
            if (typeof showToast === 'function') {
                showToast('success', 'Feedback successfully submitted!');
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
            e.preventDefault();
            editProfileModal.style.display = 'flex';
        });
    }

    if (closeEditProfileBtn) {
        closeEditProfileBtn.addEventListener('click', () => {
            editProfileModal.style.display = 'none';
        });
    }

    // =======================================================
    // RESERVATION MODAL LOGIC
    // =======================================================
    const openReservationBtn = document.getElementById('openReservationBtn');
    const reservationModal = document.getElementById('reservationModal');
    const closeReservationBtn = document.getElementById('closeReservationBtn');

    if (openReservationBtn) {
        openReservationBtn.addEventListener('click', (e) => {
            e.preventDefault();
            reservationModal.style.display = 'flex';
        });
    }
    if (closeReservationBtn) {
        closeReservationBtn.addEventListener('click', () => {
            reservationModal.style.display = 'none';
        });
    }

    // =======================================================
    // FEEDBACK MODAL LOGIC
    // =======================================================
    const openFeedbackBtn = document.getElementById('openFeedbackBtn');
    const feedbackModal = document.getElementById('feedbackModal');
    const closeFeedbackBtn = document.getElementById('closeFeedbackBtn');

    if (openFeedbackBtn) {
        openFeedbackBtn.addEventListener('click', (e) => {
            e.preventDefault();
            feedbackModal.style.display = 'flex';
        });
    }
    if (closeFeedbackBtn) {
        closeFeedbackBtn.addEventListener('click', () => {
            feedbackModal.style.display = 'none';
        });
    }

    // =======================================================
    // CLOSE ALL MODALS ON OUTSIDE CLICK
    // =======================================================
    window.addEventListener('click', function(e) {
        if (editProfileModal && e.target === editProfileModal) editProfileModal.style.display = 'none';
        if (reservationModal && e.target === reservationModal) reservationModal.style.display = 'none';
        if (feedbackModal && e.target === feedbackModal) feedbackModal.style.display = 'none';
    });

});

// =======================================================
// INSTAGRAM-STYLE PROFILE PICTURE PREVIEW
// (Naa sa gawas aron matawag diritso sa HTML onchange)
// =======================================================
function previewImage(event) {
    var reader = new FileReader();
    reader.onload = function() {
        var output = document.getElementById('profilePreview');
        output.src = reader.result;
    };
    reader.readAsDataURL(event.target.files[0]);
}