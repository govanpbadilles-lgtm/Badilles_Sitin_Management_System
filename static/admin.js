// =======================================================
// ADMIN DASHBOARD JAVASCRIPT
// =======================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. I-check kung naay ?login=success sa link para sa Toast Notification
    const urlParams = new URLSearchParams(window.location.search);
    
 if (urlParams.get('sitin') === 'success') {
        setTimeout(() => {
            if (typeof showToast === 'function') showToast('success', 'Student successfully sat in!');
        }, 100);
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // =======================================================
    // SEARCH MODAL LOGIC (GISULOD NATO DIRE PARA MOGANA)
    // =======================================================
    const searchNavBtn = document.getElementById('searchNavBtn');
    const searchModal = document.getElementById('searchModal');
    const closeSearchBtn = document.getElementById('closeSearchBtn');
    const executeSearchBtn = document.getElementById('executeSearchBtn');
    const searchResults = document.getElementById('searchResults');

    // =======================================================
    // VIEW RECORDS MODAL LOGIC
    // =======================================================
    const openRecordsBtn = document.getElementById('openRecordsBtn');
    const recordsModal = document.getElementById('recordsModal');
    const closeRecordsBtn = document.getElementById('closeRecordsBtn');

    if (openRecordsBtn) {
        openRecordsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            recordsModal.style.display = 'flex';
        });
    }

    if (closeRecordsBtn) {
        closeRecordsBtn.addEventListener('click', () => {
            recordsModal.style.display = 'none';
        });
    }

    // Isira ang modal kung mo-click sa gawas
    window.addEventListener('click', function(e) {
        if (e.target === recordsModal) {
            recordsModal.style.display = 'none';
        }
    });

    // I-open ang modal inig click sa navbar
    if (searchNavBtn) {
        searchNavBtn.addEventListener('click', function(e) {
            e.preventDefault();
            searchModal.style.display = 'flex';
            searchResults.style.display = 'none'; // I-hide ang daan nga resulta
            document.getElementById('searchInputID').value = ''; // Limpyohan ang textbox
        });
    }

    // I-close ang modal
    if (closeSearchBtn) {
        closeSearchBtn.addEventListener('click', () => searchModal.style.display = 'none');
    }

    // Isira ang modal kung mo-click sa gawas
    window.addEventListener('click', function(e) {
        if (e.target === searchModal) {
            searchModal.style.display = 'none';
        }
    });

    // Inig click sa "Search" button sulod sa modal
    if (executeSearchBtn) {
        executeSearchBtn.addEventListener('click', function() {
            const idNumber = document.getElementById('searchInputID').value;
            
            if (idNumber.trim() === '') {
                alert("Please enter an ID Number!");
                return;
            }

            // Mo-request sa Python gamit ang Fetch API
            fetch(`/search_student?id_number=${idNumber}`)
                .then(response => response.json())
                .then(data => {
                    searchResults.style.display = 'block';
                    
                if (data.found) {
                        // Kung nakit-an, i-display ang SIT-IN FORM
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
                        // Kung wala nakit-an nga ID
                        searchResults.innerHTML = `<p style="color: red; font-weight: bold; text-align: center;"><i class="fas fa-exclamation-triangle"></i> ${data.message}</p>`;
                    }
                })
                .catch(error => console.error('Error fetching data:', error));
        });
    }

}); 

// =======================================================
    // ACTIVE SIT-INS MODAL LOGIC
    // =======================================================
    const openActiveBtn = document.getElementById('openActiveBtn');
    const activeModal = document.getElementById('activeModal');
    const closeActiveBtn = document.getElementById('closeActiveBtn');

    if (openActiveBtn) {
        openActiveBtn.addEventListener('click', function(e) {
            e.preventDefault();
            activeModal.style.display = 'flex';
        });
    }

    if (closeActiveBtn) {
        closeActiveBtn.addEventListener('click', () => {
            activeModal.style.display = 'none';
        });
    }

    // Isira ang modal kung mo-click sa gawas
    window.addEventListener('click', function(e) {
        if (e.target === activeModal) {
            activeModal.style.display = 'none';
        }
    });