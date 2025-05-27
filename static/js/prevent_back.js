/**
 * Smart Supply Support System (4S) - Prevent Back Navigation After Logout
 */

(function() {
    // Prevent access to this page after logout
    if (sessionStorage.getItem('authenticated') === null) {
        sessionStorage.setItem('authenticated', 'true');
    }
    
    // Disable browser back button after logout
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            // Page was loaded from cache (back button)
            location.reload();
        }
    });
    
    // Check for logout cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    
    if (getCookie('logged_out') === 'true') {
        // Clear session storage and redirect to login
        sessionStorage.removeItem('authenticated');
        window.location.href = '/login';
    }
    
    // Add event listener to detect when user navigates away
    window.addEventListener('beforeunload', function() {
        // This will be triggered when the user navigates away from the page
    });
    
    // Prevent back navigation with history API
    history.pushState(null, null, location.href);
    window.onpopstate = function() {
        history.go(1);
    };
})();