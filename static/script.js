document.addEventListener('DOMContentLoaded', function() {
    
    // =======================================================
    // PART 1: HOME PAGE LOGIC (Login Modal)
    // =======================================================
    
    // We try to find the modal first. If it exists, we know we are on the Home Page.
    const loginModal = document.getElementById("loginModal");

    if (loginModal) {
        const loginBtn = document.getElementById("loginLink");
        const closeBtn = document.querySelector(".close-btn");

        // 1. OPEN MODAL: When "Login" is clicked
        if (loginBtn) {
            loginBtn.addEventListener('click', function(event) {
                event.preventDefault(); // Stop the link from jumping
                loginModal.style.display = "flex"; // Show and center it
            });
        }

        // 2. CLOSE MODAL: When "X" is clicked
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                loginModal.style.display = "none"; // Hide it
            });
        }

        // 3. CLOSE MODAL: When clicking outside the glass card
        window.addEventListener('click', function(event) {
            if (event.target === loginModal) {
                loginModal.style.display = "none";
            }
        });
    }


    // =======================================================
    // PART 2: REGISTER PAGE LOGIC (Form Validation)
    // =======================================================

    // We try to find the form. If it exists, we know we are on the Register Page.
    const regForm = document.getElementById('regForm');

    if (regForm) {
        regForm.addEventListener('submit', function(event) {
            // Get the values inside the event listener to get the LATEST typing
            const pass1 = document.getElementById('password').value;
            const pass2 = document.getElementById('confirm_password').value;

            // Check if they match
            if (pass1 !== pass2) {
                event.preventDefault(); // Stop the form from sending data
                alert("Passwords do not match! Please try again.");
            }
        });
    }

});