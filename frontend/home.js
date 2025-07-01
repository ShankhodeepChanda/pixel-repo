// Search handling
function handleSearch(query) {
    if (query.trim()) {
        window.location.href = query;
    }
}

// Theme management
function setTheme(isDark) {
    document.body.className = isDark ? 'dark' : '';
}

// Initialization
function initialize() {
    // Focus search box
    const searchBox = document.querySelector('.search-box');
    if (searchBox) {
        searchBox.focus();
    }
}

// Run when page loads
window.addEventListener('load', initialize);

// Expose functions globally for Python integration
window.AdaptaHome = {
    handleSearch,
    setTheme
};
