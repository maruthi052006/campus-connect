// CampusConnect Central JavaScript
// Handles CSRF, API wrappers, and recurring global events.

// Extract CSRF token from cookies
const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];

/**
 * Standard fetch wrapper that automatically applies CSRF tokens and JSON headers.
 * @param {string} url - Target URL.
 * @param {Object} data - JavaScript object to send as payload.
 * @param {string} method - HTTP method (default 'POST').
 */
async function fetchAPI(url, data, method = 'POST') {
  const options = {
    method: method,
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    }
  };
  
  if (data !== null && method !== 'GET' && method !== 'HEAD') {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(url, options);
  if (!response.ok) {
    let errText = await response.text();
    console.error('API Error:', errText);
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Global AJAX bindings for Feed interactions
 */
document.addEventListener('DOMContentLoaded', () => {
    // Hydrate Like states from hidden markers securely rendered by Django
    document.querySelectorAll('.user-has-liked-marker').forEach(marker => {
        const btn = document.querySelector(`.like-post-btn[data-post-id="${marker.dataset.postId}"]`);
        if (btn) {
            btn.classList.add('active', 'text-danger');
            const icon = btn.querySelector('i');
            if(icon) {
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill', 'text-danger');
            }
        }
    });

    // Hydrate Save states
    document.querySelectorAll('.user-has-saved-marker').forEach(marker => {
        const btn = document.querySelector(`.save-post-btn[data-post-id="${marker.dataset.postId}"]`);
        if (btn) {
            btn.classList.add('text-primary');
            const icon = btn.querySelector('i');
            if(icon) {
                icon.classList.remove('bi-bookmark');
                icon.classList.add('bi-bookmark-fill');
            }
        }
    });

    // Like Button Toggle
    document.addEventListener('click', async (e) => {
        const likeBtn = e.target.closest('.like-post-btn');
        if (likeBtn) {
            e.preventDefault();
            const postId = likeBtn.dataset.postId;
            if (!postId) return;
            
            try {
                const res = await fetchAPI('/post/like/', { post_id: postId });
                const icon = likeBtn.querySelector('i');
                const countSpan = likeBtn.querySelector('.like-count');
                if (res.liked) {
                    icon.classList.remove('bi-heart');
                    icon.classList.add('bi-heart-fill', 'text-danger');
                    likeBtn.classList.add('active', 'text-danger');
                } else {
                    icon.classList.remove('bi-heart-fill', 'text-danger');
                    icon.classList.add('bi-heart');
                    likeBtn.classList.remove('active', 'text-danger');
                }
                if (countSpan && res.count !== undefined) {
                    countSpan.textContent = res.count;
                }
            } catch (err) {
                console.error("Failed to toggle like", err);
            }
        }
    });

    // Save Button Toggle
    document.addEventListener('click', async (e) => {
        const saveBtn = e.target.closest('.save-post-btn');
        if (saveBtn) {
            e.preventDefault();
            const postId = saveBtn.dataset.postId;
            if (!postId) return;
            
            try {
                const res = await fetchAPI('/post/save/', { post_id: postId });
                const icon = saveBtn.querySelector('i');
                if (res.saved) {
                    icon.classList.remove('bi-bookmark');
                    icon.classList.add('bi-bookmark-fill', 'text-primary');
                    saveBtn.classList.add('text-primary');
                } else {
                    icon.classList.remove('bi-bookmark-fill', 'text-primary');
                    icon.classList.add('bi-bookmark');
                    saveBtn.classList.remove('text-primary');
                }
            } catch (err) {
                console.error("Failed to toggle save", err);
            }
        }
    });

    // Follow Button Toggle
    document.addEventListener('click', async (e) => {
        const followBtn = e.target.closest('.follow-btn');
        if (followBtn) {
            e.preventDefault();
            const userId = followBtn.dataset.userId;
            if (!userId) return;

            try {
                const res = await fetchAPI('/connections/follow/', { user_id: userId });
                if (res.status === 'success') {
                    if (res.following) {
                        followBtn.textContent = 'Following';
                        followBtn.classList.replace('btn-primary-cc', 'btn-outline-cc');
                    } else {
                        followBtn.textContent = 'Follow';
                        followBtn.classList.replace('btn-outline-cc', 'btn-primary-cc');
                    }
                }
            } catch (err) {
                console.error("Failed to toggle follow", err);
            }
        }
    });

    // Sidebar and Mobile Nav Active State
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav-item, .mobile-nav-item').forEach(item => {
        const link = item.getAttribute('href') || (item.dataset.link ? '/' + item.dataset.link + '/' : null);
        if (link && (currentPath === link || (link !== '/' && currentPath.startsWith(link)))) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Form Submit Spinners
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.classList.contains('no-spinner')) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = originalText;
                submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...`;
            }
        });
    });

    // Image Preview Helper
    document.querySelectorAll('.image-preview-input').forEach(input => {
        input.addEventListener('change', function() {
            const targetId = this.dataset.previewTarget;
            const target = document.getElementById(targetId);
            if (target && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = e => target.src = e.target.result;
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // Image Lightbox Logic
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('.lightbox-trigger');
        if (trigger) {
            const modalEl = document.getElementById('lightboxModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                const lightboxImg = document.getElementById('lightboxImg');
                if (lightboxImg) {
                    lightboxImg.src = trigger.src;
                    modal.show();
                }
            }
        }
    });
});

/**
 * Global Toast Notification
 * @param {string} message 
 * @param {string} type - 'success', 'danger', 'info', 'warning'
 */
function showToast(message, type = 'success', url = null) {
    let container = document.querySelector('.toast-container-global');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container-global position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1090';
        container.style.marginTop = '60px';
        document.body.appendChild(container);
    }

    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'text-bg-success' : (type === 'danger' ? 'text-bg-danger' : (type === 'warning' ? 'text-bg-warning' : (type === 'info' ? 'text-bg-info' : 'text-bg-primary')));
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true" style="cursor: ${url ? 'pointer' : 'default'};">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(toastId);
    if (url) {
        toastEl.addEventListener('click', (e) => {
            if (!e.target.closest('.btn-close')) {
                window.location.href = url;
            }
        });
    }
    const bsToast = new bootstrap.Toast(toastEl, { delay: 5000 });
    bsToast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

/**
 * Notification Badge Polling
 */
let lastNotifCount = -1; // Initialize to -1 to avoid toast on first load if count > 0
async function pollNotifications() {
    try {
        const response = await fetch('/notifications/unread-count/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (response.ok) {
            const data = await response.json();
            const badge = document.getElementById('notifBadge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count > 9 ? '9+' : data.count;
                    badge.style.display = 'inline-block';
                    
                    // Show toast if count increased and this is not the first poll
                    if (lastNotifCount !== -1 && data.count > lastNotifCount) {
                        const msg = data.latest_msg || 'You have a new notification!';
                        const url = data.latest_url || null;
                        showToast(msg, 'info', url);
                    }
                } else {
                    badge.style.display = 'none';
                }
                lastNotifCount = data.count;
            }
        }
    } catch (err) {
        console.warn('Silent notification poll failed');
    }
}

// Start polling every 5 seconds if logged in
if (document.cookie.includes('sessionid')) {
    setInterval(pollNotifications, 5000);
    pollNotifications(); // initial check
}

// Global Sidebar Drawer Toggle (Mobile)
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.left-sidebar');
    const toggleBtn = document.getElementById('sidebarToggleGlobal');
    const overlay = document.getElementById('mainOverlay');

    if (sidebar && toggleBtn && overlay) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.add('show');
            overlay.classList.add('active');
        });

        overlay.addEventListener('click', () => {
            sidebar.classList.remove('show');
            overlay.classList.remove('active');
        });

        // Close sidebar when clicking a link
        sidebar.querySelectorAll('.sidebar-item').forEach(link => {
            link.addEventListener('click', () => {
                sidebar.classList.remove('show');
                overlay.classList.remove('active');
            });
        });
    }
});
