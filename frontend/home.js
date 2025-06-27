// Search handling
function handleSearch(query) {
    if (query.trim()) {
        window.location.href = query;
    }
}

// Time update functionality
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
    });
    const timeElement = document.querySelector('#current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

// Theme management
function setTheme(isDark) {
    document.body.className = isDark ? 'dark' : '';
}

// Initialization
function initialize() {
    // Start time updates
    setInterval(updateTime, 1000);

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
    updateTime,
    setTheme
};
