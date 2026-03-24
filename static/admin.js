// =======================================================
// ADMIN DASHBOARD JAVASCRIPT
// =======================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. I-check ang URL kung unsay i-toast
    const urlParams = new URLSearchParams(window.location.search);
    
    // Para sa Toast Notification kung naay ni sit-in
    if (urlParams.get('sitin') === 'success') {
        setTimeout(() => {
            if (typeof showToast === 'function') showToast('success', 'Student successfully sat in!');
        }, 100);
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // =======================================================
    // SEARCH MODAL LOGIC (PARA TIME-IN)
    // =======================================================
    const searchNavBtn = document.getElementById('searchNavBtn');
    const searchModal = document.getElementById('searchModal');
    const closeSearchBtn = document.getElementById('closeSearchBtn');
    const executeSearchBtn = document.getElementById('executeSearchBtn');
    const searchResults = document.getElementById('searchResults');

    if (searchNavBtn) {
        searchNavBtn.addEventListener('click', function(e) {
            e.preventDefault();
            searchModal.style.display = 'flex';
            searchResults.style.display = 'none'; 
            document.getElementById('searchInputID').value = ''; 
        });
    }

    if (closeSearchBtn) {
        closeSearchBtn.addEventListener('click', () => searchModal.style.display = 'none');
    }

    window.addEventListener('click', function(e) {
        if (e.target === searchModal) {
            searchModal.style.display = 'none';
        }
    });

    if (executeSearchBtn) {
        executeSearchBtn.addEventListener('click', function() {
            const idNumber = document.getElementById('searchInputID').value;
            
            if (idNumber.trim() === '') {
                alert("Please enter an ID Number!");
                return;
            }

            fetch(`/search_student?id_number=${idNumber}`)
                .then(response => response.json())
                .then(data => {
                    searchResults.style.display = 'block';
                    
                if (data.found) {
                        searchResults.innerHTML = `
                            <form action="/sit_in" method="POST" style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
                                <input type="hidden" name="id_number" value="${data.id_number}">
                                <div style="background: #e9ecef; padding: 15px; border-radius: 8px; margin-bottom: 5px;">
                                    <p style="margin: 0 0 5px 0; color: #1b4f8a;"><strong>Student Name:</strong> ${data.name}</p>
                                    <p style="margin: 0;"><strong>Remaining Sessions:</strong> <span style="color: red; font-weight: bold; font-size: 16px;">${data.remaining_sessions}</span></p>
                                </div>
                                <label style="font-weight: bold; color: #333;">Select Lab:</label>
                                <select name="lab" required style="padding: 10px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px;">
                                    <option value="" disabled selected>-- Choose Laboratory --</option>
                                    <option value="Lab 524">Lab 524</option>
                                    <option value="Lab 526">Lab 526</option>
                                    <option value="Lab 528">Lab 528</option>
                                    <option value="Lab 530">Lab 530</option>
                                    <option value="Lab 542">Lab 542</option>
                                    <option value="Lab 544">Lab 544</option>
                                    <option value="Mac Lab">Mac Lab</option>
                                </select>
                                <label style="font-weight: bold; color: #333; margin-top: 5px;">Purpose:</label>
                                <select name="purpose" required style="padding: 10px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px;">
                                    <option value="" disabled selected>-- Choose Purpose --</option>
                                    <option value="C Programming">C Programming</option>
                                    <option value="Java Programming">Java Programming</option>
                                    <option value="Python Programming">Python Programming</option>
                                    <option value="Web Development">Web Development</option>
                                    <option value="Data Structures">Data Structures</option>
                                    <option value="Others">Others</option>
                                </select>
                                <button type="submit" class="btn-post" style="margin-top: 15px; background: #1b4f8a; font-size: 16px;">
                                    <i class="fas fa-sign-in-alt"></i> Sit-in Student
                                </button>
                            </form>
                        `;
                    } else {
                        searchResults.innerHTML = `<p style="color: red; font-weight: bold; text-align: center;"><i class="fas fa-exclamation-triangle"></i> ${data.message}</p>`;
                    }
                })
                .catch(error => console.error('Error fetching data:', error));
        });
    }

    // =======================================================
    // ADD STUDENT MODAL LOGIC
    // =======================================================
    const addStudentModal = document.getElementById("addStudentModal");
    const btnAdd = document.querySelector(".btn-add"); 
    const closeAddBtn = document.getElementById("closeAddBtn");

    if (btnAdd && addStudentModal) {
        btnAdd.addEventListener("click", function() {
            addStudentModal.style.display = "flex";
        });
    }

    if (closeAddBtn && addStudentModal) {
        closeAddBtn.addEventListener("click", function() {
            addStudentModal.style.display = "none";
        });
    }

    window.addEventListener("click", function(event) {
        if (event.target === addStudentModal) {
            addStudentModal.style.display = "none";
        }
    });

    // =======================================================
    // EDIT STUDENT MODAL LOGIC
    // =======================================================
    const editStudentModal = document.getElementById("editStudentModal");
    const closeEditBtn = document.getElementById("closeEditBtn");
    const editForm = document.getElementById("editStudentForm");
    const editButtons = document.querySelectorAll(".action-edit");

    editButtons.forEach(btn => {
        btn.addEventListener("click", function() {
            const id = this.getAttribute("data-id");
            const fname = this.getAttribute("data-firstname");
            const mname = this.getAttribute("data-middlename");
            const lname = this.getAttribute("data-lastname");
            const course = this.getAttribute("data-course");
            const level = this.getAttribute("data-level");

            if(editForm) editForm.action = `/edit_student/${id}`;

            if(document.getElementById("edit_firstname")) document.getElementById("edit_firstname").value = fname;
            if(document.getElementById("edit_middlename")) document.getElementById("edit_middlename").value = mname;
            if(document.getElementById("edit_lastname")) document.getElementById("edit_lastname").value = lname;
            if(document.getElementById("edit_course")) document.getElementById("edit_course").value = course;
            if(document.getElementById("edit_level")) document.getElementById("edit_level").value = level;

            if(editStudentModal) editStudentModal.style.display = "flex";
        });
    });

    if (closeEditBtn && editStudentModal) {
        closeEditBtn.addEventListener("click", function() {
            editStudentModal.style.display = "none";
        });
    }

    window.addEventListener("click", function(event) {
        if (event.target === editStudentModal) {
            editStudentModal.style.display = "none";
        }
    });

    // =======================================================
    // REAL-TIME SEARCH SA MASTERLIST TABLE
    // =======================================================
    const masterlistSearch = document.getElementById('masterlistSearch');
    
    if (masterlistSearch) {
        masterlistSearch.addEventListener('keyup', function() {
            let filter = this.value.toLowerCase();
            let rows = document.querySelectorAll('.modern-table tbody tr');

            rows.forEach(row => {
                if (row.cells.length === 1) return; 

                let rowText = row.textContent.toLowerCase();
                if (rowText.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

});