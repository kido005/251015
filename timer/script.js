const timeElement = document.getElementById('clock-time');
const dateElement = document.getElementById('clock-date');

const timeFormatter = new Intl.DateTimeFormat('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
});

const dateFormatter = new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
});

function updateClock() {
    const now = new Date();
    const isoString = now.toISOString();
    timeElement.textContent = timeFormatter.format(now);
    timeElement.setAttribute('datetime', isoString);
    dateElement.textContent = dateFormatter.format(now);
}

updateClock(); // initialize immediately
setInterval(updateClock, 1000);
