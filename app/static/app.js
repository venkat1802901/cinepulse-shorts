let activeFilter = 'all';
let approvedCount = 0;

// Countdown to 11:30 AM IST
function updateCountdown() {
  const now = new Date();
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
  const istNow = new Date(utc + (3600000 * 5.5));

  let deadline = new Date(istNow);
  deadline.setHours(11, 30, 0, 0);

  if (istNow > deadline) {
    deadline.setDate(deadline.getDate() + 1);
  }

  const diffMs = deadline - istNow;
  const hrs = Math.floor(diffMs / 3600000);
  const mins = Math.floor((diffMs % 3600000) / 60000);
  const secs = Math.floor((diffMs % 60000) / 1000);

  const timerEl = document.getElementById('timer-display');
  if (timerEl) {
    timerEl.innerText = `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
}

setInterval(updateCountdown, 1000);
updateCountdown();

// Notification Permission Handler
async function requestNotificationPermission() {
  if (!('Notification' in window)) {
    showToast('⚠️ Notifications are not supported in this browser.');
    return;
  }

  try {
    const permission = await Notification.requestPermission();
    const notifBtn = document.getElementById('notif-btn');

    if (permission === 'granted') {
      if (notifBtn) {
        notifBtn.classList.add('active');
        notifBtn.innerHTML = `🔔 Alerts Active`;
      }
      showToast('🎉 Notifications enabled! Sending test alert...');

      // Trigger test notification
      if ('serviceWorker' in navigator) {
        const reg = await navigator.serviceWorker.ready;
        reg.showNotification('🎬 CinePulse Daily Alerts Active!', {
          body: 'You will receive notifications every morning at 3:30 AM when fresh viral edits are ready!',
          icon: '/static/icon-192.png',
          badge: '/static/icon-192.png',
          vibrate: [200, 100, 200]
        });
      } else {
        new Notification('🎬 CinePulse Daily Alerts Active!', {
          body: 'You will receive notifications every morning when fresh viral edits are ready!',
          icon: '/static/icon-192.png'
        });
      }
    } else {
      showToast('Notification permission was denied.');
    }
  } catch (err) {
    console.error('Notification error:', err);
    showToast('Could not enable notifications.');
  }
}

// Check existing permission on page load
function checkExistingNotificationStatus() {
  if ('Notification' in window && Notification.permission === 'granted') {
    const notifBtn = document.getElementById('notif-btn');
    if (notifBtn) {
      notifBtn.classList.add('active');
      notifBtn.innerHTML = `🔔 Alerts Active`;
    }
  }
}

// Copy to clipboard helper
function copyText(elementId, btnElement, label) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.getAttribute('data-raw') || el.innerText;
  navigator.clipboard.writeText(text).then(() => {
    btnElement.classList.add('copied');
    btnElement.innerHTML = `✓ Copied`;
    showToast(`Copied ${label} to clipboard!`);
    setTimeout(() => {
      btnElement.classList.remove('copied');
      btnElement.innerHTML = `📋 Copy ${label}`;
    }, 2000);
  });
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.innerText = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}

// Toggle Approval State (Max 2)
function toggleApprove(btn, cardId) {
  const card = document.getElementById(cardId);
  const isApproved = card.classList.contains('approved');

  if (!isApproved && approvedCount >= 2) {
    showToast('⚠️ You have already approved your 2 daily videos!');
    return;
  }

  if (isApproved) {
    card.classList.remove('approved');
    btn.classList.remove('active');
    btn.innerHTML = `⭐ Approve Video`;
    approvedCount--;
  } else {
    card.classList.add('approved');
    btn.classList.add('active');
    btn.innerHTML = `✅ Approved (Ready)`;
    approvedCount++;
    showToast('🎉 Video approved! Ready for YouTube Studio upload.');
  }

  document.getElementById('approved-counter').innerText = approvedCount;
}

// Filter handling
function setFilter(lang) {
  activeFilter = lang;
  document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
  document.getElementById(`filter-${lang}`).classList.add('active');

  document.querySelectorAll('.video-card').forEach(card => {
    if (lang === 'all' || card.getAttribute('data-lang') === lang) {
      card.style.display = 'block';
    } else {
      card.style.display = 'none';
    }
  });
}

// Deep-link to YouTube Studio Upload
function openYouTubeStudio() {
  const isAndroid = /Android/i.test(navigator.userAgent);
  if (isAndroid) {
    window.location.href = 'intent://studio.youtube.com/#Intent;package=com.google.android.apps.youtube.creator;scheme=https;end';
    setTimeout(() => window.open('https://studio.youtube.com', '_blank'), 500);
  } else {
    window.open('https://studio.youtube.com', '_blank');
  }
}

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then(() => {
      checkExistingNotificationStatus();
    }).catch(err => console.log('SW failed', err));
  });
}
