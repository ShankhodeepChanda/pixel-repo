// Browser functionality
const webview = document.getElementById('webview');
const urlInput = document.getElementById('url-input');
const backButton = document.getElementById('back');
const forwardButton = document.getElementById('forward');
const reloadButton = document.getElementById('reload');

// History management
let history = ['https://www.apple.com'];
let currentIndex = 0;

// Function to check if input is a URL
function isValidURL(string) {
  try {
    new URL(string);
    return true;
  } catch (_) {
    // Check for domain-like patterns without protocol
    const domainPattern = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/;
    const localPattern = /^localhost(:\d+)?$/;
    return domainPattern.test(string) || localPattern.test(string) || string.includes('.');
  }
}

// Function to format URL
function formatURL(input) {
  input = input.trim();

  if (!input) return '';

  // If it's already a valid URL, return as is
  if (input.startsWith('http://') || input.startsWith('https://')) {
    return input;
  }

  // If it looks like a domain, add https://
  if (isValidURL(input)) {
    return 'https://' + input;
  }

  // Otherwise, treat as search query
  return 'https://www.google.com/search?q=' + encodeURIComponent(input);
}

// Function to navigate to URL
function navigateToURL(url) {
  if (!url) return;

  const formattedURL = formatURL(url);
  webview.src = formattedURL;

  // Add to history if it's different from current
  if (history[currentIndex] !== formattedURL) {
    // Remove any forward history
    history = history.slice(0, currentIndex + 1);
    // Add new URL
    history.push(formattedURL);
    currentIndex = history.length - 1;
  }

  // Update URL input to show the formatted URL
  urlInput.value = formattedURL;

  // Update button states
  updateNavigationButtons();
}

// Function to update navigation button states
function updateNavigationButtons() {
  backButton.disabled = currentIndex <= 0;
  forwardButton.disabled = currentIndex >= history.length - 1;

  // Update button styles
  backButton.style.opacity = backButton.disabled ? '0.5' : '1';
  forwardButton.style.opacity = forwardButton.disabled ? '0.5' : '1';
}

// Event listeners
urlInput.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') {
    navigateToURL(this.value);
  }
});

urlInput.addEventListener('focus', function () {
  this.select(); // Select all text when focusing
});

backButton.addEventListener('click', function () {
  if (currentIndex > 0) {
    currentIndex--;
    const url = history[currentIndex];
    webview.src = url;
    urlInput.value = url;
    updateNavigationButtons();
  }
});

forwardButton.addEventListener('click', function () {
  if (currentIndex < history.length - 1) {
    currentIndex++;
    const url = history[currentIndex];
    webview.src = url;
    urlInput.value = url;
    updateNavigationButtons();
  }
});

reloadButton.addEventListener('click', function () {
  webview.src = webview.src; // Reload current page
});

// Handle iframe load events
webview.addEventListener('load', function () {
  try {
    // Update URL input with actual loaded URL
    if (webview.contentWindow && webview.contentWindow.location.href !== 'about:blank') {
      urlInput.value = webview.contentWindow.location.href;
    }
  } catch (e) {
    // Cross-origin restrictions prevent access to iframe content
    // This is normal for external websites
  }
});

// Initialize navigation buttons
updateNavigationButtons();

// Set initial URL in input
urlInput.value = history[currentIndex];

function changeTheme() {
  document.body.classList.toggle('dark');
}
