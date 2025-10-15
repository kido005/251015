const clockTimeEl = document.getElementById('clock-time');
const clockDateEl = document.getElementById('clock-date');
const clockMsEl = document.getElementById('clock-ms');
const clockAmPmEl = document.getElementById('clock-ampm');
const cityNameEl = document.getElementById('city-name');
const timezoneLabelEl = document.getElementById('timezone-label');
const subtitleEl = document.getElementById('subtitle');
const languageToggle = document.getElementById('language-toggle');
const mapHeadingEl = document.getElementById('map-heading');
const mapInstructionEl = document.getElementById('map-instruction');
const mapDayNightOverlay = document.getElementById('map-day-night');

const localeMap = {
    ko: 'ko-KR',
    en: 'en-US'
};

const translations = {
    ko: {
        subtitle: '지금의 순간을 확인하세요',
        mapHeading: '주요 도시',
        mapInstruction: '지도에서 도시를 선택해 타임존을 변경하세요.',
        toggleText: 'EN',
        toggleAria: '영어로 변경',
        dayWord: '낮',
        nightWord: '밤',
        dayStatus: '낮 시간대',
        nightStatus: '밤 시간대'
    },
    en: {
        subtitle: 'Keep track of every moment',
        mapHeading: 'Key Cities',
        mapInstruction: 'Select a city to change the time zone.',
        toggleText: 'KO',
        toggleAria: 'Switch to Korean',
        dayWord: 'Day',
        nightWord: 'Night',
        dayStatus: 'Daytime',
        nightStatus: 'Nighttime'
    }
};

const cities = [
    {
        id: 'los-angeles',
        timeZone: 'America/Los_Angeles',
        names: { ko: '로스앤젤레스', en: 'Los Angeles' },
        country: { ko: '미국', en: 'USA' }
    },
    {
        id: 'new-york',
        timeZone: 'America/New_York',
        names: { ko: '뉴욕', en: 'New York' },
        country: { ko: '미국', en: 'USA' }
    },
    {
        id: 'saopaulo',
        timeZone: 'America/Sao_Paulo',
        names: { ko: '상파울루', en: 'S\u00e3o Paulo' },
        country: { ko: '브라질', en: 'Brazil' }
    },
    {
        id: 'london',
        timeZone: 'Europe/London',
        names: { ko: '런던', en: 'London' },
        country: { ko: '영국', en: 'United Kingdom' }
    },
    {
        id: 'paris',
        timeZone: 'Europe/Paris',
        names: { ko: '파리', en: 'Paris' },
        country: { ko: '프랑스', en: 'France' }
    },
    {
        id: 'dubai',
        timeZone: 'Asia/Dubai',
        names: { ko: '두바이', en: 'Dubai' },
        country: { ko: '아랍에미리트', en: 'United Arab Emirates' }
    },
    {
        id: 'mumbai',
        timeZone: 'Asia/Kolkata',
        names: { ko: '뭄바이', en: 'Mumbai' },
        country: { ko: '인도', en: 'India' }
    },
    {
        id: 'seoul',
        timeZone: 'Asia/Seoul',
        names: { ko: '서울', en: 'Seoul' },
        country: { ko: '대한민국', en: 'South Korea' }
    },
    {
        id: 'tokyo',
        timeZone: 'Asia/Tokyo',
        names: { ko: '도쿄', en: 'Tokyo' },
        country: { ko: '일본', en: 'Japan' }
    },
    {
        id: 'sydney',
        timeZone: 'Australia/Sydney',
        names: { ko: '시드니', en: 'Sydney' },
        country: { ko: '호주', en: 'Australia' }
    }
];

const cityData = new Map(cities.map((city) => [city.id, city]));
const cityElements = new Map();

document.querySelectorAll('.map__city').forEach((button) => {
    const id = button.dataset.cityId;
    if (!id || !cityData.has(id)) {
        return;
    }
    cityElements.set(id, {
        button,
        label: button.querySelector('.map__label'),
        status: button.querySelector('.map__status')
    });
});

let language = 'ko';
let currentCityId = cityData.has('seoul') ? 'seoul' : cities[0].id;
let currentTimeZone = cityData.get(currentCityId).timeZone;
let lastSecond = null;
let lastMinute = null;
let timezoneDirty = true;

const timeFormatterCache = new Map();
const dateFormatterCache = new Map();
const timeZoneNameFormatterCache = new Map();

function getTimeFormatter(timeZone) {
    const key = timeZone;
    if (!timeFormatterCache.has(key)) {
        timeFormatterCache.set(
            key,
            new Intl.DateTimeFormat('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true,
                timeZone
            })
        );
    }
    return timeFormatterCache.get(key);
}

function getDateFormatter(locale, timeZone) {
    const key = `${locale}|${timeZone}`;
    if (!dateFormatterCache.has(key)) {
        dateFormatterCache.set(
            key,
            new Intl.DateTimeFormat(locale, {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'long',
                timeZone
            })
        );
    }
    return dateFormatterCache.get(key);
}

function getTimeZoneNameFormatter(locale, timeZone) {
    const key = `${locale}|${timeZone}`;
    if (!timeZoneNameFormatterCache.has(key)) {
        timeZoneNameFormatterCache.set(
            key,
            new Intl.DateTimeFormat(locale, {
                hour: 'numeric',
                timeZone,
                timeZoneName: 'longGeneric'
            })
        );
    }
    return timeZoneNameFormatterCache.get(key);
}

function getZonedDate(date, timeZone) {
    const utcDate = new Date(date.toLocaleString('en-US', { timeZone: 'UTC' }));
    const tzDate = new Date(date.toLocaleString('en-US', { timeZone }));
    const diff = tzDate.getTime() - utcDate.getTime();
    return new Date(date.getTime() + diff);
}

function getTimezoneOffset(timeZone, date) {
    const utcDate = new Date(date.toLocaleString('en-US', { timeZone: 'UTC' }));
    const tzDate = new Date(date.toLocaleString('en-US', { timeZone }));
    return (tzDate.getTime() - utcDate.getTime()) / 60000;
}

function formatOffset(offsetMinutes) {
    const sign = offsetMinutes >= 0 ? '+' : '-';
    const absolute = Math.abs(offsetMinutes);
    const hours = String(Math.floor(absolute / 60)).padStart(2, '0');
    const minutes = String(absolute % 60).padStart(2, '0');
    return `GMT${sign}${hours}:${minutes}`;
}

function triggerAnimation(element, className) {
    if (!element) {
        return;
    }
    element.classList.remove(className);
    // Force reflow to restart the animation.
    void element.offsetWidth;
    element.classList.add(className);
}

function updateCitiesLanguage() {
    cities.forEach((city) => {
        const entry = cityElements.get(city.id);
        if (!entry) {
            return;
        }
        entry.label.textContent = city.names[language];
    });
}

function highlightActiveCity() {
    cityElements.forEach((entry, id) => {
        entry.button.classList.toggle('map__city--active', id === currentCityId);
    });
}

function updateActiveCityUI() {
    const city = cityData.get(currentCityId);
    if (!city) {
        return;
    }
    const cityName = city.names[language];
    const countryName = city.country[language];
    if (cityNameEl) {
        cityNameEl.textContent = `${cityName}, ${countryName}`;
    }
    highlightActiveCity();
}

function updateTimezoneLabel(date) {
    if (!timezoneLabelEl) {
        return;
    }
    const locale = localeMap[language];
    const formatter = getTimeZoneNameFormatter(locale, currentTimeZone);
    const parts = formatter.formatToParts(date);
    const namePart = parts.find((part) => part.type === 'timeZoneName');
    const offsetMinutes = getTimezoneOffset(currentTimeZone, date);
    const timeZoneName = namePart ? namePart.value : currentTimeZone.replace(/_/g, ' ');
    timezoneLabelEl.textContent = `${timeZoneName} (${formatOffset(offsetMinutes)})`;
}

function updateDayNightOverlay(date) {
    if (!mapDayNightOverlay) {
        return;
    }
    const minutes = date.getUTCHours() * 60 + date.getUTCMinutes();
    const rotation = (minutes / 1440) * 360;
    mapDayNightOverlay.style.setProperty('--sun-rotation', `${(-rotation).toFixed(2)}deg`);
}

function updateCitiesStatus(date) {
    const translation = translations[language];
    cities.forEach((city) => {
        const entry = cityElements.get(city.id);
        if (!entry) {
            return;
        }
        const zonedDate = getZonedDate(date, city.timeZone);
        const hour = zonedDate.getHours();
        const isDay = hour >= 6 && hour < 18;
        entry.button.dataset.day = isDay ? 'true' : 'false';
        entry.status.textContent = isDay ? '☀' : '🌙';
        const cityName = city.names[language];
        const countryName = city.country[language];
        const statusText = isDay ? translation.dayStatus : translation.nightStatus;
        entry.button.setAttribute('aria-label', `${cityName}, ${countryName}. ${statusText}.`);
        entry.button.setAttribute('title', `${cityName} · ${isDay ? translation.dayWord : translation.nightWord}`);
    });
}

function applyLanguage() {
    const translation = translations[language];
    document.documentElement.lang = language;
    if (subtitleEl) {
        subtitleEl.textContent = translation.subtitle;
    }
    if (mapHeadingEl) {
        mapHeadingEl.textContent = translation.mapHeading;
    }
    if (mapInstructionEl) {
        mapInstructionEl.textContent = translation.mapInstruction;
    }
    if (languageToggle) {
        languageToggle.textContent = translation.toggleText;
        languageToggle.setAttribute('aria-label', translation.toggleAria);
        languageToggle.setAttribute('title', translation.toggleAria);
    }
    updateCitiesLanguage();
    updateActiveCityUI();
    timezoneDirty = true;
    lastMinute = null;
    lastSecond = null;
    updateClock(true);
}

function setCurrentCity(cityId) {
    if (!cityData.has(cityId)) {
        return;
    }
    currentCityId = cityId;
    currentTimeZone = cityData.get(cityId).timeZone;
    timezoneDirty = true;
    lastMinute = null;
    lastSecond = null;
    updateActiveCityUI();
    updateClock(true);
}

function updateClock(force = false) {
    const now = new Date();
    if (force) {
        lastSecond = null;
        lastMinute = null;
    }

    const zonedDate = getZonedDate(now, currentTimeZone);
    if (clockMsEl) {
        clockMsEl.textContent = `.${String(zonedDate.getMilliseconds()).padStart(3, '0')}`;
    }
    const currentSecond = zonedDate.getSeconds();
    const currentMinute = zonedDate.getMinutes();

    if (force || currentSecond !== lastSecond) {
        lastSecond = currentSecond;
        const formatter = getTimeFormatter(currentTimeZone);
        const parts = formatter.formatToParts(now);
        const hour = parts.find((part) => part.type === 'hour')?.value ?? '00';
        const minute = parts.find((part) => part.type === 'minute')?.value ?? '00';
        const second = parts.find((part) => part.type === 'second')?.value ?? '00';
        const dayPeriod = parts.find((part) => part.type === 'dayPeriod')?.value ?? '';

        if (clockTimeEl) {
            clockTimeEl.textContent = `${hour}:${minute}:${second}`;
            clockTimeEl.setAttribute('datetime', zonedDate.toISOString());
        }
        if (clockAmPmEl) {
            clockAmPmEl.textContent = dayPeriod.toUpperCase();
        }

        if (force || currentMinute !== lastMinute) {
            lastMinute = currentMinute;
            const locale = localeMap[language];
            const dateFormatter = getDateFormatter(locale, currentTimeZone);
            if (clockDateEl) {
                clockDateEl.textContent = dateFormatter.format(now);
            }
            triggerAnimation(clockTimeEl, 'animate-minute');
            triggerAnimation(clockAmPmEl, 'animate-minute');
            timezoneDirty = true;
        } else {
            triggerAnimation(clockTimeEl, 'animate-second');
        }

        triggerAnimation(clockMsEl, 'animate-second');
        updateCitiesStatus(now);
        updateDayNightOverlay(now);
        if (timezoneDirty) {
            updateTimezoneLabel(now);
            timezoneDirty = false;
        }
    }
}

if (languageToggle) {
    languageToggle.addEventListener('click', () => {
        language = language === 'ko' ? 'en' : 'ko';
        applyLanguage();
    });
}

cityElements.forEach((entry, id) => {
    entry.button.addEventListener('click', () => setCurrentCity(id));
});

applyLanguage();
setInterval(() => updateClock(), 50);
