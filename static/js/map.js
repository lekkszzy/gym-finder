// Adapted from my Lab 4 map.js (cities) for the Dublin Gym Finder

// ===== Map setup =====
const DUBLIN = [53.3498, -6.2603];
const DEFAULT_ZOOM = 12;

const map = L.map('map').setView(DUBLIN, DEFAULT_ZOOM);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
    minZoom: 7
}).addTo(map);

// ===== State =====
let gymsData = [];   // GeoJSON features from the API
let markers = {};    // gym id -> marker

const GYMS_URL = '/api/gyms/';

// Cluster group holds all gym markers
const clusterGroup = L.markerClusterGroup({
    showCoverageOnHover: false,
    maxClusterRadius: 50
});
map.addLayer(clusterGroup);

// ===== Load data =====
async function initMap() {
    try {
        const response = await fetch(GYMS_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();   // GeoJSON FeatureCollection
        gymsData = data.features;

        showGyms(gymsData);

    } catch (error) {
        console.error('Error fetching gyms:', error);
        showMessage('Failed to load gyms. Make sure the API is running.');
    }
}

// ===== Markers (clustered) + results list =====
function clearMarkers() {
    clusterGroup.clearLayers();
    markers = {};
}

function showGyms(features) {
    clearMarkers();

    features.forEach(feature => {
        const [lng, lat] = feature.geometry.coordinates;   // GeoJSON is [lng, lat]
        const gym = feature.properties;

        // 24/7 gyms get a green marker, others blue
        const marker = L.circleMarker([lat, lng], {
            radius: 8,
            fillColor: gym.is_24_hours_open ? '#198754' : '#0d6efd',
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
        });

        marker.bindPopup(createPopupContent(gym));
        marker.bindTooltip(gym.name);

        clusterGroup.addLayer(marker);
        markers[feature.id] = marker;
    });

    showResultsList(features);
}

function showResultsList(features) {
    const list = document.getElementById('results');
    document.getElementById('resultCount').textContent = features.length;

    if (features.length === 0) {
        list.innerHTML = '<li class="list-group-item text-muted">No gyms found</li>';
        return;
    }

    list.innerHTML = features.map(f => `
        <li class="list-group-item list-group-item-action" role="button" tabindex="0" data-id="${f.id}">
            <strong>${escapeHtml(f.properties.name)}</strong><br>
            <span class="text-muted">${formatPrice(f.properties.monthly_price)}</span>
        </li>
    `).join('');
}

// Click (or Enter key) on a result -> go to that gym
document.getElementById('results').addEventListener('click', e => {
    const item = e.target.closest('[data-id]');
    if (item) goToGym(item.dataset.id);
});
document.getElementById('results').addEventListener('keydown', e => {
    const item = e.target.closest('[data-id]');
    if (item && e.key === 'Enter') goToGym(item.dataset.id);
});

// ===== Popup =====
function createPopupContent(gym) {
    const hours = gym.is_24_hours_open
        ? 'Open 24/7'
        : (gym.opening_time && gym.closing_time
            ? `${gym.opening_time.slice(0, 5)} – ${gym.closing_time.slice(0, 5)}`
            : 'Hours not listed');

    const facilities = gym.facilities.length
        ? gym.facilities.map(f => escapeHtml(f.name)).join(', ')
        : 'None listed';

    return `
        <div class="gym-popup">
            <h3 class="h6 mb-1">${escapeHtml(gym.name)}</h3>
            ${gym.address ? `<p class="mb-1">${escapeHtml(gym.address)}</p>` : ''}
            <p class="mb-1"><strong>Price:</strong> ${formatPrice(gym.monthly_price)}</p>
            <p class="mb-1"><strong>Hours:</strong> ${hours}</p>
            <p class="mb-1"><strong>Facilities:</strong> ${facilities}</p>
            ${gym.website ? `<a href="${escapeHtml(gym.website)}" target="_blank" rel="noopener">Visit website</a>` : ''}
        </div>
    `;
}

function formatPrice(price) {
    return price ? `€${Number(price).toFixed(2)} / month` : 'Price not listed';
}

// Stops HTML in gym names etc. from being run in the page (XSS protection)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== Navigate to gym (works with clusters) =====
function goToGym(gymId) {
    const marker = markers[gymId];
    if (!marker) return;

    clusterGroup.zoomToShowLayer(marker, () => {
        map.setView(marker.getLatLng(), Math.max(map.getZoom(), 15));
        marker.openPopup();
    });
}

// ===== Messages (instead of alert) =====
function showMessage(text) {
    document.getElementById('message').textContent = text;
}

// ===== Reset =====
document.getElementById('resetBtn').addEventListener('click', function () {
    map.setView(DUBLIN, DEFAULT_ZOOM);
    showMessage('');
    showGyms(gymsData);
});

initMap();