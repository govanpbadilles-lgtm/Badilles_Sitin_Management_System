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
                                <select name="lab" id="sitInLabSelect" required style="padding: 10px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px;">
                                    <option value="" disabled selected>-- Choose Laboratory --</option>
                                    <option value="Lab 524">Lab 524</option>
                                    <option value="Lab 526">Lab 526</option>
                                    <option value="Lab 528">Lab 528</option>
                                    <option value="Lab 530">Lab 530</option>
                                    <option value="Lab 542">Lab 542</option>
                                    <option value="Lab 544">Lab 544</option>
                                </select>

                                <label style="font-weight: bold; color: #333;">Select PC:</label>
                                <select name="pc_number" id="sitInPcSelect" required style="padding: 10px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px;">
                                    <option value="" disabled selected>-- Select Laboratory First --</option>
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

                        // Add event listener for lab selection to fetch PCs
                        document.getElementById('sitInLabSelect').addEventListener('change', function() {
                            const lab = this.value;
                            const pcSelect = document.getElementById('sitInPcSelect');
                            pcSelect.innerHTML = '<option value="" disabled selected>Loading PCs...</option>';

                            fetch(`/api/get_lab_pcs?lab=${encodeURIComponent(lab)}`)
                                .then(r => r.json())
                                .then(pcs => {
                                    pcSelect.innerHTML = '<option value="" disabled selected>-- Choose PC --</option>';
                                    pcs.forEach(pc => {
                                        const isAvailable = pc.status === 'Working';
                                        const option = document.createElement('option');
                                        option.value = pc.pc_number;
                                        option.textContent = `PC ${pc.pc_number} - ${pc.status}`;
                                        if (!isAvailable) {
                                            option.disabled = true;
                                            option.style.color = '#ccc';
                                        }
                                        pcSelect.appendChild(option);
                                    });
                                })
                                .catch(() => {
                                    pcSelect.innerHTML = '<option value="" disabled selected>Error loading PCs</option>';
                                });
                        });

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

/* ══════════════════════════════════════════
   GLOBAL NAVIGATION & SIDEBAR LOGIC
══════════════════════════════════════════ */

function toggleSidebar() {
    var sidebar   = document.getElementById('sidebar');
    var overlay   = document.getElementById('sidebarOverlay');
    var hamburger = document.getElementById('hamburgerBtn');
    if (!sidebar || !overlay || !hamburger) return;

    var isOpen    = sidebar.classList.contains('open');
    if (isOpen) {
        sidebar.classList.remove('open');
        overlay.classList.remove('visible');
        hamburger.classList.remove('open');
    } else {
        sidebar.classList.add('open');
        overlay.classList.add('visible');
        hamburger.classList.add('open');
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        var sidebar = document.getElementById('sidebar');
        if (sidebar && sidebar.classList.contains('open')) {
            toggleSidebar();
        }
    }
});

/* ── SIDEBAR SEARCH LINK ── */
document.addEventListener('DOMContentLoaded', function() {
    const sbSearch = document.getElementById('sb-search');
    if (sbSearch) {
        sbSearch.addEventListener('click', function(e) {
            e.preventDefault();
            const sidebar = document.getElementById('sidebar');
            if (sidebar && sidebar.classList.contains('open')) toggleSidebar();
            
            const modal = document.getElementById('searchModal');
            if (modal) {
                modal.style.display = 'flex';
                const input = document.getElementById('searchInputID');
                if (input) {
                    input.value = '';
                    input.focus();
                }
                const results = document.getElementById('searchResults');
                if (results) results.style.display = 'none';
            }
        });
    }

    /* ── PC MANAGEMENT ── */
    const sbPcMgmt = document.getElementById('sb-pc-mgmt');
    if (sbPcMgmt) {
        sbPcMgmt.addEventListener('click', function(e) {
            e.preventDefault();
            const sidebar = document.getElementById('sidebar');
            if (sidebar && sidebar.classList.contains('open')) toggleSidebar();
            
            const modal = document.getElementById('pcMgmtModal');
            if (modal) {
                modal.style.display = 'flex';
                if (typeof loadPcStatuses === 'function') loadPcStatuses();
            }
        });
    }

    /* ── AI ASSISTANT ── */
    const sbAi = document.getElementById('sb-ai');
    if (sbAi) {
        sbAi.addEventListener('click', function(e) {
            e.preventDefault();
            const sidebar = document.getElementById('sidebar');
            if (sidebar && sidebar.classList.contains('open')) toggleSidebar();
            
            const modal = document.getElementById('aiModal');
            if (modal) {
                modal.style.display = 'flex';
                if (typeof loadChatHistory === 'function') loadChatHistory();
            }
        });
    }
});

/* ══════════════════════════════════════════
   GLOBAL MODAL LOGIC (PC, AI, SEARCH)
══════════════════════════════════════════ */

// PC MAINTENANCE
function loadPcStatuses() {
    const labSelect = document.getElementById('labSelect');
    if (!labSelect) return;
    const lab = labSelect.value;
    const grid = document.getElementById('pcGrid');
    if (!grid) return;
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #888;"><i class="fas fa-circle-notch fa-spin"></i> Loading PCs...</div>';

    fetch('/api/get_lab_pcs?lab=' + encodeURIComponent(lab))
        .then(r => r.json())
        .then(pcs => {
            grid.innerHTML = '';
            pcs.forEach(pc => {
                const card = document.createElement('div');
                const statusCls = pc.status.toLowerCase().replace(/ /g, '-');
                const isEnabled = pc.availability === 'Enabled';
                
                card.className = `pc-card ${statusCls} ${isEnabled ? '' : 'disabled'}`;
                
                let icon = 'fa-desktop';
                if (pc.status === 'Under Maintenance') icon = 'fa-tools';
                else if (pc.status === 'No Internet Connection') icon = 'fa-wifi-slash';
                else if (pc.status === 'Hardware Issue') icon = 'fa-microchip';
                else if (pc.status === 'Software Issue') icon = 'fa-code-branch';
                else if (pc.status === 'Not Working') icon = 'fa-exclamation-triangle';
                else if (pc.status === 'Occupied') icon = 'fa-user-clock';

                card.innerHTML = `
                    <i class="fas ${icon}"></i>
                    <span>PC ${pc.pc_number}</span>
                    <span class="pc-status-label">${pc.status}</span>
                `;
                card.onclick = () => openEditPcModal(lab, pc);
                grid.appendChild(card);
            });
        })
        .catch(err => {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #ff4c4c;">Failed to load PCs.</div>';
        });
}

function openEditPcModal(lab, pc) {
    const modal = document.getElementById('editPcModal');
    if (!modal) return;
    document.getElementById('editPcLab').value = lab;
    document.getElementById('editPcNumber').value = pc.pc_number;
    document.getElementById('editPcTitle').innerHTML = `<i class="fas fa-edit"></i> Manage ${lab} - PC ${pc.pc_number}`;
    document.getElementById('editPcStatus').value = pc.status === 'Occupied' ? 'Working' : pc.status;
    document.getElementById('editPcRemarks').value = pc.remarks || '';
    document.getElementById('editPcLastUpdated').textContent = pc.last_updated || 'Never';
    
    if (pc.availability === 'Enabled') document.getElementById('availEnabled').checked = true;
    else document.getElementById('availDisabled').checked = true;

    modal.style.display = 'flex';
}

function savePcStatus() {
    const lab = document.getElementById('editPcLab').value;
    const pc_number = document.getElementById('editPcNumber').value;
    const status = document.getElementById('editPcStatus').value;
    const remarks = document.getElementById('editPcRemarks').value;
    
    const availEl = document.querySelector('input[name="availability"]:checked');
    const availability = availEl ? availEl.value : 'Enabled';

    fetch('/api/update_pc_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lab, pc_number, status, availability, remarks })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (typeof showToast === 'function') {
                showToast('success', 'PC ' + pc_number + ' updated successfully.');
            } else {
                alert('PC ' + pc_number + ' updated successfully.');
            }
            document.getElementById('editPcModal').style.display = 'none';
            loadPcStatuses();
        }
    })
    .catch(err => {
        console.error('Error updating PC status:', err);
    });
}

// AI CHAT ASSISTANT
function appendMessage(type, text, time) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    const div = document.createElement('div');
    div.className = `chat-bubble ${type}`;
    
    let timestamp = 'Just now';
    if (time) {
        try {
            const d = new Date(time.replace(' ', 'T'));
            timestamp = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch(e) { timestamp = 'Recent'; }
    }

    div.innerHTML = `${text}<span class="chat-time">${timestamp}</span>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function loadChatHistory() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    chatMessages.innerHTML = '';
    fetch('/api/chat/history')
        .then(r => r.json())
        .then(history => {
            if (history.length === 0) {
                appendMessage('ai', 'Hello Admin! I am your SITIN Management Assistant. I can help you with lab stats, student counts, and system guidance.', null);
            } else {
                history.forEach(msg => {
                    appendMessage(msg.type, msg.text, msg.time);
                });
            }
        });
}

// NOTIFICATIONS SYSTEM
(function() {
    var POLL_INTERVAL = 30000;
    var prevCount = null;
    var dropdownOpen = false;
    var ICONS = { reservation: 'fa-calendar-check', approved: 'fa-check-circle', declined: 'fa-times-circle', announcement: 'fa-bullhorn' };

    window.toggleNotifDropdown = function(e) {
        if (e) e.stopPropagation();
        var dd = document.getElementById('notifDropdown');
        if (!dd) return;
        dropdownOpen = !dropdownOpen;
        dd.style.display = dropdownOpen ? 'block' : 'none';
        if (dropdownOpen) loadNotifications();
    };

    function loadNotifications() {
        fetch('/notifications/list').then(r => r.json()).then(items => {
            var list = document.getElementById('notifList');
            if (!list) return;
            if (!items || items.length === 0) {
                list.innerHTML = '<div class="notif-empty"><i class="fas fa-bell-slash"></i><p>No notifications yet</p></div>';
                return;
            }
            list.innerHTML = '';
            items.forEach(item => {
                var icon = ICONS[item.type] || 'fa-bell';
                var unread = item.is_read === 0;
                var div = document.createElement('div');
                div.className = 'notif-item' + (unread ? ' unread' : '');
                div.innerHTML = `<div class="notif-icon ${item.type}"><i class="fas ${icon}"></i></div>
                                 <div class="notif-body"><p class="notif-msg">${item.message}</p>
                                 <span class="notif-time">${item.created_at}</span></div>
                                 ${unread ? '<div class="notif-unread-dot"></div>' : ''}`;
                div.onclick = () => {
                    fetch('/notifications/read/' + item.id, { method: 'POST' });
                    if (item.link) window.location.href = item.link;
                };
                list.appendChild(div);
            });
        });
    }

    function fetchCount() {
        fetch('/notifications/count').then(r => r.json()).then(data => {
            var count = data.count || 0;
            var badge = document.getElementById('notifBadge');
            if (badge) {
                if (count > 0) { badge.style.display = 'flex'; badge.textContent = count > 99 ? '99+' : count; }
                else { badge.style.display = 'none'; }
            }
            if (prevCount !== null && count > prevCount) {
                var btn = document.getElementById('notifBellBtn');
                if (btn) btn.classList.add('shake');
            }
            prevCount = count;
        });
    }

    setInterval(fetchCount, POLL_INTERVAL);
    document.addEventListener('DOMContentLoaded', fetchCount);
})();

document.addEventListener('DOMContentLoaded', function() {
    const closePcMgmt = document.getElementById('closePcMgmtBtn');
    if (closePcMgmt) closePcMgmt.onclick = () => document.getElementById('pcMgmtModal').style.display = 'none';
    
    const closeEditPc = document.getElementById('closeEditPcBtn');
    if (closeEditPc) closeEditPc.onclick = () => document.getElementById('editPcModal').style.display = 'none';
    
    const closeAi = document.getElementById('closeAIBtn');
    if (closeAi) closeAi.onclick = () => document.getElementById('aiModal').style.display = 'none';

    const pcForm = document.getElementById('editPcForm');
    if (pcForm) {
        pcForm.onsubmit = (e) => { e.preventDefault(); savePcStatus(); };
    }

    const aiForm = document.getElementById('chatForm');
    if (aiForm) {
        aiForm.onsubmit = (e) => {
            e.preventDefault();
            const input = document.getElementById('chatInput');
            const msg = input.value.trim();
            if (!msg) return;
            appendMessage('user', msg, null);
            input.value = '';
            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            })
            .then(r => r.json())
            .then(data => { if (data.response) appendMessage('ai', data.response, null); });
        };
    }
});

/* ── NOTIFICATION DROPDOWN ── */
function toggleNotifDropdown(e) {
    if (e) e.stopPropagation();
    const dd = document.getElementById('notifDropdown');
    if (dd) {
        dd.style.display = dd.style.display === 'none' ? 'block' : 'none';
    }
}

document.addEventListener('click', function(e) {
    const dd = document.getElementById('notifDropdown');
    const bell = document.getElementById('notifBellBtn');
    if (dd && dd.style.display === 'block') {
        if (!dd.contains(e.target) && !bell.contains(e.target)) {
            dd.style.display = 'none';
        }
    }
});