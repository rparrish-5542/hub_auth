// Discover Endpoints - Filter and Selection Management

document.addEventListener('DOMContentLoaded', function() {
    // Filter checkbox auto-submit
    const filterCheckboxes = document.querySelectorAll('#filterForm input[type="checkbox"]');
    filterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            document.getElementById('filterForm').submit();
        });
    });

    // Select All / Deselect All
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.endpoint-checkbox');
            checkboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
        });
    }

    // Submit button validation
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            const checked = document.querySelectorAll('.endpoint-checkbox:checked');
            if (checked.length === 0) {
                e.preventDefault();
                alert('Please select at least one endpoint to create permissions.');
                return false;
            }
            if (!confirm('Create permissions for ' + checked.length + ' endpoint(s)?')) {
                e.preventDefault();
                return false;
            }
        });
    }

    // Cancel button
    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) {
        const cancelUrl = cancelBtn.getAttribute('data-cancel-url');
        cancelBtn.addEventListener('click', function() {
            if (cancelUrl) {
                window.location.href = cancelUrl;
            }
        });
    }

    // Back button
    const backBtn = document.getElementById('backBtn');
    if (backBtn) {
        const backUrl = backBtn.getAttribute('data-back-url');
        backBtn.addEventListener('click', function() {
            if (backUrl) {
                window.location.href = backUrl;
            }
        });
    }
});
