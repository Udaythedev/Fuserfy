document.addEventListener('DOMContentLoaded', function() {
    // ===== Sidebar Toggle (Mobile) =====
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebar = document.getElementById('sidebar');
    const modalOverlay = document.getElementById('modalOverlay');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.add('active');
            modalOverlay.classList.add('active');
        });
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', function() {
            closeSidebar();
        });
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', function() {
            closeSidebar();
        });
    }

    function closeSidebar() {
        sidebar.classList.remove('active');
        modalOverlay.classList.remove('active');
    }

    // ===== Delete Playlist Modal =====
    const deleteModal = document.getElementById('deleteModal');
    const cancelDeleteBtn = document.getElementById('cancelDelete');
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    let pendingDeletePlaylistId = null;

    // Attach handlers to delete buttons
    document.querySelectorAll('.delete-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const playlistId = this.getAttribute('data-playlist-id');
            const playlistName = this.getAttribute('data-playlist-name');
            
            // Show modal
            pendingDeletePlaylistId = playlistId;
            document.getElementById('deletePlaylistName').textContent = '"' + playlistName + '"';
            deleteModal.classList.add('active');
            modalOverlay.classList.add('active');
        });
    });

    // Cancel delete
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', function() {
            deleteModal.classList.remove('active');
            modalOverlay.classList.remove('active');
            pendingDeletePlaylistId = null;
        });
    }

    // Confirm delete
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            if (pendingDeletePlaylistId) {
                // Create hidden form and submit
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/delete_playlist';
                
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'playlist_id';
                input.value = pendingDeletePlaylistId;
                
                form.appendChild(input);
                document.body.appendChild(form);
                form.submit();
            }
        });
    }

    // Close modal when clicking overlay
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === modalOverlay && deleteModal.classList.contains('active')) {
                deleteModal.classList.remove('active');
                modalOverlay.classList.remove('active');
            }
        });
    }

    // ===== Form Validation =====
    const addSongsForm = document.getElementById('addSongsForm');
    if (addSongsForm) {
        addSongsForm.addEventListener('submit', function(e) {
            const playlistSelect = document.getElementById('playlistSelect');
            const songList = document.getElementById('songList');

            if (!playlistSelect.value) {
                e.preventDefault();
                alert('Please select a playlist before adding songs.');
                playlistSelect.focus();
                return false;
            }

            if (!songList.value.trim()) {
                e.preventDefault();
                alert('Please enter at least one song name.');
                songList.focus();
                return false;
            }
        });
    }

    // ===== Keyboard Navigation =====
    document.addEventListener('keydown', function(e) {
        // Close modal with Escape key
        if (e.key === 'Escape') {
            deleteModal.classList.remove('active');
            modalOverlay.classList.remove('active');
            closeSidebar();
        }
    });

    // ===== Accessibility: Close modal with Escape from modal buttons =====
    const modalButtons = document.querySelectorAll('.modal-actions button');
    modalButtons.forEach(function(btn) {
        btn.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                deleteModal.classList.remove('active');
                modalOverlay.classList.remove('active');
            }
        });
    });
});

