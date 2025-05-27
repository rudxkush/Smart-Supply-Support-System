/**
 * Smart Supply Support System (4S) - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Prevent form resubmission on page refresh
    if (window.history.replaceState) {
        window.history.replaceState(null, null, window.location.href);
    }
    
    // Handle product selection in submit request form
    setupProductSelection();
    
    // Setup tab navigation
    setupTabs();
    
    // Setup search functionality
    setupSearch();
    
    // Setup mobile navigation
    setupMobileNav();
});

/**
 * Setup product selection functionality
 */
function setupProductSelection() {
    const productSelect = document.getElementById('product');
    const newProductFields = document.getElementById('new-product-fields');
    const mainQuantity = document.getElementById('main_quantity');
    const productAvailability = document.getElementById('product-availability');
    
    if (productSelect) {
        productSelect.addEventListener('change', function() {
            if (this.value === 'new_product') {
                newProductFields.style.display = 'block';
                mainQuantity.parentElement.style.display = 'none';
                productAvailability.innerHTML = '<div class="alert alert-info">New product will be added to inventory and forwarded to production.</div>';
            } else if (this.value !== '') {
                newProductFields.style.display = 'none';
                mainQuantity.parentElement.style.display = 'block';
                
                // Extract product status and quantity from the selected option text
                const optionText = productSelect.options[productSelect.selectedIndex].text;
                if (optionText.includes('In Stock')) {
                    productAvailability.innerHTML = '<div class="alert alert-success">Product is in stock and available for immediate delivery.</div>';
                } else if (optionText.includes('Low Stock')) {
                    productAvailability.innerHTML = '<div class="alert alert-warning">Product is in low stock. Order may be partially fulfilled.</div>';
                } else if (optionText.includes('Out of Stock')) {
                    productAvailability.innerHTML = '<div class="alert alert-danger">Product is out of stock. Request will be forwarded to production.</div>';
                }
            } else {
                newProductFields.style.display = 'none';
                mainQuantity.parentElement.style.display = 'block';
                productAvailability.innerHTML = '';
            }
        });
    }
}

/**
 * Setup tab navigation
 */
function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    const requestsTable = document.getElementById('requestsTable');
    
    if (tabs.length > 0 && requestsTable) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                // Add active class to clicked tab
                this.classList.add('active');
                
                const filter = this.getAttribute('data-filter');
                const rows = requestsTable.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    if (filter === 'all') {
                        row.style.display = '';
                    } else {
                        const status = row.getAttribute('data-status');
                        if (status && status.includes(filter)) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    }
                });
            });
        });
    }
}

/**
 * Setup search functionality
 */
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const requestsTable = document.getElementById('requestsTable');
    
    if (searchInput && requestsTable) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = searchInput.value.toLowerCase();
            const rows = requestsTable.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

/**
 * Setup mobile navigation
 */
function setupMobileNav() {
    const sidebar = document.querySelector('.sidebar');
    const mobileMenuToggle = document.createElement('button');
    mobileMenuToggle.className = 'mobile-menu-toggle';
    mobileMenuToggle.innerHTML = '<span class="material-icons">menu</span>';
    
    if (sidebar && window.innerWidth < 768) {
        document.querySelector('header').appendChild(mobileMenuToggle);
        
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show-mobile');
        });
    }
}

/**
 * Show a confirmation dialog
 * @param {string} message - The confirmation message
 * @returns {boolean} - True if confirmed, false otherwise
 */
function confirmAction(message) {
    return confirm(message);
}

/**
 * Format date to a readable format
 * @param {string} dateString - The date string to format
 * @returns {string} - Formatted date string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Validate form before submission
 * @param {HTMLFormElement} form - The form to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    return isValid;
}