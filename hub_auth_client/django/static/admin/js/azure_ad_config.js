// Azure AD Configuration - Sensitive Field Reveal Toggle

function toggleReveal(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) {
        console.error('Field not found:', fieldId);
        return;
    }
    
    const isRevealed = field.classList.contains('revealed');
    
    if (isRevealed) {
        // Hide the value
        field.classList.remove('revealed');
        field.classList.add('masked');
        
        // Restore masked text
        const originalValue = field.dataset.value;
        if (fieldId.includes('tenant_id') || fieldId.includes('client_id')) {
            // For GUIDs, show last 12 characters
            field.textContent = '••••••••-••••-••••-••••-' + originalValue.slice(-12);
        } else if (fieldId.includes('client_secret')) {
            // For secrets, show all bullets
            const maskedLength = Math.min(originalValue.length, 40);
            field.textContent = '•'.repeat(maskedLength);
        }
    } else {
        // Reveal the value
        field.classList.remove('masked');
        field.classList.add('revealed');
        field.textContent = field.dataset.value;
        
        // Auto-hide after 30 seconds
        setTimeout(() => {
            if (field.classList.contains('revealed')) {
                toggleReveal(fieldId);
            }
        }, 30000);
    }
}

// Add event listeners when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Azure AD Config: Initializing reveal buttons');
    
    // Attach click handlers to all reveal buttons
    const revealButtons = document.querySelectorAll('.reveal-btn');
    console.log('Found reveal buttons:', revealButtons.length);
    
    revealButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const fieldId = this.getAttribute('data-field-id');
            console.log('Reveal button clicked for field:', fieldId);
            if (fieldId) {
                toggleReveal(fieldId);
            }
        });
    });
});
