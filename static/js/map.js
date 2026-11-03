// Adapted from my Lab 4 map.js (cities) for the Dublin Gym Finder

// ===== Map setup =====
const DUBLIN = [53.3498, -6.2603];
const DEFAULT_ZOOM = 12;

const map = L.map('map').setView(DUBLIN, DEFAULT_ZOOM);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
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
            ? `${gym.opening_time.slice(0, 5)} &ndash; ${gym.closing_time.slice(0, 5)}`
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
    return price ? `&euro;${Number(price).toFixed(2)} / month` : 'Price not listed';
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
    showMessage('');
    clearSearchShapes();
    resetShapeStyles();
    document.getElementById('areaSelect').value = '';
    document.getElementById('routeSelect').value = '';
    if (searchMarker) {
        map.removeLayer(searchMarker);
        searchMarker = null;
    }
    searchPoint = null;
    showGyms(gymsData);
    map.fitBounds(clusterGroup.getBounds(), { padding: [30, 30] });
});

// ===== Search point (my location or a click on the map) =====
let searchPoint = null;     // {lat, lng}
let searchMarker = null;    // blue dot showing the search point
let radiusCircle = null;    // circle drawn for radius searches

function setSearchPoint(lat, lng, label) {
    searchPoint = { lat, lng };

    if (searchMarker) map.removeLayer(searchMarker);
    searchMarker = L.circleMarker([lat, lng], {
        radius: 9,
        fillColor: '#dc3545',
        color: '#ffffff',
        weight: 3,
        fillOpacity: 1
    }).addTo(map).bindTooltip(label, { permanent: false });

    showMessage('');
}

// Click anywhere on the map to set the search point
map.on('click', e => {
    setSearchPoint(e.latlng.lat, e.latlng.lng, 'Search point');
});

// "Use my location" uses the browser's Geolocation API (via Leaflet)
document.getElementById('locateBtn').addEventListener('click', () => {
    showMessage('Finding your location...');
    map.locate({ setView: true, maxZoom: 14 });
});

map.on('locationfound', e => {
    setSearchPoint(e.latlng.lat, e.latlng.lng, 'You are here');
});

map.on('locationerror', () => {
    showMessage('Could not get your location. Click on the map instead.');
});

// ===== Radius slider label =====
const radiusInput = document.getElementById('radius');
radiusInput.addEventListener('input', () => {
    document.getElementById('radiusValue').textContent = radiusInput.value;
});

// ===== Calling the spatial API =====
async function fetchGyms(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            // The API sends {"error": "..."} for bad input (400)
            showMessage(data.error || `Request failed (status ${response.status})`);
            return null;
        }
        return data;
    } catch (error) {
        console.error('Search failed:', error);
        showMessage('Search failed. Make sure the API is running.');
        return null;
    }
}

function clearSearchShapes() {
    if (radiusCircle) {
        map.removeLayer(radiusCircle);
        radiusCircle = null;
    }
}

function needSearchPoint() {
    if (!searchPoint) {
        showMessage('Click on the map or use your location first.');
        return true;
    }
    return false;
}

// Nearest gyms -> GET /api/gyms/nearest/
document.getElementById('nearestBtn').addEventListener('click', async () => {
    if (needSearchPoint()) return;
    clearSearchShapes();

    const params = new URLSearchParams({ lat: searchPoint.lat, lng: searchPoint.lng, limit: 5 });
    const data = await fetchGyms(`/api/gyms/nearest/?${params}`);
    if (!data) return;

    showGyms(data.gyms.features);
    fitToResults(data.gyms.features);
});

// Gyms within radius -> GET /api/gyms/within-radius/
document.getElementById('radiusBtn').addEventListener('click', async () => {
    if (needSearchPoint()) return;
    clearSearchShapes();

    const radiusKm = Number(radiusInput.value);
    const params = new URLSearchParams({ lat: searchPoint.lat, lng: searchPoint.lng, radius_km: radiusKm });
    const data = await fetchGyms(`/api/gyms/within-radius/?${params}`);
    if (!data) return;

    // Draw the search circle (Leaflet circle radius is in metres)
    radiusCircle = L.circle([searchPoint.lat, searchPoint.lng], {
        radius: radiusKm * 1000,
        color: '#0d6efd',
        fillOpacity: 0.08
    }).addTo(map);
    map.fitBounds(radiusCircle.getBounds());

    showGyms(data.gyms.features);
    if (data.gyms.features.length === 0) showMessage(`No gyms within ${radiusKm} km.`);
});

// Zoom the map to show all results
function fitToResults(features) {
    if (features.length === 0) return;
    const points = features.map(f => [f.geometry.coordinates[1], f.geometry.coordinates[0]]);
    if (searchPoint) points.push([searchPoint.lat, searchPoint.lng]);
    map.fitBounds(points, { padding: [40, 40], maxZoom: 15 });
}

// ===== Areas (polygons) and routes (lines) =====
const areaLayer = L.featureGroup().addTo(map);    // all area polygons
const routeLayer = L.featureGroup().addTo(map);   // all route lines
let areaShapes = {};    // area id -> polygon
let routeShapes = {};   // route id -> line

const AREA_STYLE = { color: '#6f42c1', weight: 2, fillOpacity: 0.08 };
const AREA_HIGHLIGHT = { color: '#6f42c1', weight: 4, fillOpacity: 0.25 };
const ROUTE_STYLE = { color: '#fd7e14', weight: 4, opacity: 0.6 };
const ROUTE_HIGHLIGHT = { color: '#fd7e14', weight: 7, opacity: 1 };

// Layer control so users can switch each layer on and off
L.control.layers(null, {
    'Gyms': clusterGroup,
    'Areas': areaLayer,
    'Routes': routeLayer
}, { position: 'topright' }).addTo(map);

async function loadAreasAndRoutes() {
    const [areas, routes] = await Promise.all([fetchGyms('/api/areas/'), fetchGyms('/api/routes/')]);
    const areaSelect = document.getElementById('areaSelect');
    const routeSelect = document.getElementById('routeSelect');

    if (areas) {
        L.geoJSON(areas, {
            style: AREA_STYLE,
            onEachFeature: (feature, layer) => {
                areaShapes[feature.id] = layer;
                layer.bindTooltip(feature.properties.name);
                areaSelect.add(new Option(feature.properties.name, feature.id));
            }
        }).eachLayer(layer => areaLayer.addLayer(layer));
    }

    if (routes) {
        L.geoJSON(routes, {
            style: ROUTE_STYLE,
            onEachFeature: (feature, layer) => {
                routeShapes[feature.id] = layer;
                layer.bindTooltip(`${feature.properties.name} (by ${feature.properties.owner})`);
                routeSelect.add(new Option(feature.properties.name, feature.id));
            }
        }).eachLayer(layer => routeLayer.addLayer(layer));
    }
}

function resetShapeStyles() {
    Object.values(areaShapes).forEach(s => s.setStyle(AREA_STYLE));
    Object.values(routeShapes).forEach(s => s.setStyle(ROUTE_STYLE));
}

// Gyms in an area -> GET /api/areas/<id>/gyms/
async function searchArea(areaId) {
    if (!areaId) return;
    clearSearchShapes();
    resetShapeStyles();
    document.getElementById('routeSelect').value = '';

    const data = await fetchGyms(`/api/areas/${areaId}/gyms/`);
    if (!data) return;

    const shape = areaShapes[areaId];
    shape.setStyle(AREA_HIGHLIGHT);
    map.fitBounds(shape.getBounds(), { padding: [30, 30] });

    showGyms(data.gyms.features);
    showMessage(data.total_found === 0 ? `No gyms in ${data.area}.` : '');
}

// Gyms along a route -> GET /api/routes/<id>/gyms/?buffer_m=
async function searchRoute(routeId) {
    if (!routeId) return;
    clearSearchShapes();
    resetShapeStyles();
    document.getElementById('areaSelect').value = '';

    const bufferM = Number(document.getElementById('buffer').value);
    const params = new URLSearchParams({ buffer_m: bufferM });
    const data = await fetchGyms(`/api/routes/${routeId}/gyms/?${params}`);
    if (!data) return;

    const shape = routeShapes[routeId];
    shape.setStyle(ROUTE_HIGHLIGHT);
    shape.bringToFront();
    map.fitBounds(shape.getBounds(), { padding: [40, 40] });

    showGyms(data.gyms.features);
    showMessage(data.total_found === 0 ? `No gyms within ${bufferM} m of this route.` : '');
}

document.getElementById('areaSelect').addEventListener('change', e => searchArea(e.target.value));
document.getElementById('routeSelect').addEventListener('change', e => searchRoute(e.target.value));
// Re-run the route search when the distance changes
document.getElementById('buffer').addEventListener('change', () => {
    searchRoute(document.getElementById('routeSelect').value);
});

loadAreasAndRoutes();

initMap();