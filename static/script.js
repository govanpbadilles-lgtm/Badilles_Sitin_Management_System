/* =======================================================
   MAIN INITIALIZATION
   We use 'DOMContentLoaded' to ensure the HTML is fully 
   loaded before we try to attach any JavaScript to it.
   ======================================================= */
document.addEventListener('DOMContentLoaded', function() {
    
    // =======================================================
    // PART 1: HOME PAGE LOGIC (Login Modal)
    // =======================================================
    
    /* We attempt to find the 'loginModal'. 
       If this variable is null, it means we are NOT on the Home Page, 
       so we skip all the code inside the 'if' block to prevent errors.
    */
    const loginModal = document.getElementById("loginModal");

    if (loginModal) {
        // --- 1. Setup Variables ---
        const loginBtn = document.getElementById("loginLink"); // The "Login" link in Navbar
        const closeBtn = document.querySelector(".close-btn"); // The "X" inside the modal

        // --- 2. Open Modal Logic ---
        // Checks if the login button actually exists before adding listener
        if (loginBtn) {
            loginBtn.addEventListener('click', function(event) {
                event.preventDefault();       // STOP the link from jumping to top of page
                loginModal.style.display = "flex"; // Show the modal (Flex centers it)
            });
        }

        // --- 3. Close Modal Logic (Clicking X) ---
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                loginModal.style.display = "none"; // Hide the modal
            });
        }

        // --- 4. Close Modal Logic (Clicking Outside) ---
        // If user clicks the dark background (the modal wrapper), close it.
        // If they click the "Glass Card" inside, do nothing (let them type).
        window.addEventListener('click', function(event) {
            if (event.target === loginModal) {
                loginModal.style.display = "none";
            }
        });
    }


    // =======================================================
    // PART 2: REGISTER PAGE LOGIC (Form Validation)
    // =======================================================

    /* We attempt to find the 'regForm'. 
       If this exists, we know we are on the Register Page.
    */
    const regForm = document.getElementById('regForm');

    if (regForm) {
        
        // Listen for the "Submit" event (when user clicks Register button)
        regForm.addEventListener('submit', function(event) {
            
            // --- 1. Get Password Values ---
            // We get values *inside* the function to ensure we get what the user JUST typed.
            const pass1 = document.getElementById('password').value;
            const pass2 = document.getElementById('confirm_password').value;

            // --- 2. Compare Passwords ---
            if (pass1 !== pass2) {
                // If they don't match:
                event.preventDefault(); // STOP the form from sending data to server
                alert("Passwords do not match! Please try again."); // Show error
            }
            // If they match, the form continues to Flask automatically.
        });
    }

});