
const POPULAR_SITES = [
    { name: "Google", url: "https://www.google.com", icon: "🔍" },
    { name: "YouTube", url: "https://www.youtube.com", icon: "📺" },
    { name: "GitHub", url: "https://www.github.com", icon: "🐙" },
    { name: "Stack Overflow", url: "https://stackoverflow.com", icon: "📚" },
    { name: "Reddit", url: "https://www.reddit.com", icon: "🤖" },
    { name: "Twitter", url: "https://www.twitter.com", icon: "🐦" },
    { name: "Facebook", url: "https://www.facebook.com", icon: "📘" },
    { name: "Instagram", url: "https://www.instagram.com", icon: "📷" },
    { name: "LinkedIn", url: "https://www.linkedin.com", icon: "💼" },
    { name: "Amazon", url: "https://www.amazon.com", icon: "🛒" },
    { name: "Netflix", url: "https://www.netflix.com", icon: "🎬" },
    { name: "Spotify", url: "https://www.spotify.com", icon: "🎵" }
];

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

// Generate bookmarks HTML
function generateBookmarks() {
    const bookmarksGrid = document.getElementById('bookmarks-grid');
    if (bookmarksGrid) {
        bookmarksGrid.innerHTML = POPULAR_SITES.map(site => `
            <div class="bookmark-item" onclick="window.location.href='${site.url}'">
                <div class="bookmark-icon">${site.icon}</div>
                <div class="bookmark-name">${site.name}</div>
            </div>
        `).join('');
    }
}

// Theme management
function setTheme(isDark) {
    document.body.className = isDark ? 'dark' : '';
}

// Initialization
function initialize() {
    // Generate bookmarks if not already present
    if (document.getElementById('bookmarks-grid').innerHTML.trim() === '') {
        generateBookmarks();
    }

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
    generateBookmarks,
    setTheme,
    POPULAR_SITES
};
