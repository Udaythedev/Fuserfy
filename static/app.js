document.addEventListener('DOMContentLoaded', function() {
    // Attach handler for player control buttons to call endpoints via fetch
    document.querySelectorAll('form[data-player-control]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                body: formData
            }).then(function(resp) {
                // reload to reflect state (simple approach)
                window.location.reload();
            }).catch(function() {
                window.location.reload();
            });
        });
    });

    // Enhance delete playlist buttons to confirm
    document.querySelectorAll('form[action$="delete_playlist"]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Delete this playlist?')) {
                e.preventDefault();
            }
        });
    });
});
