/* =====================================================
   Zomato AI Frontend – app.js
   Handles: API calls, loading states, form validation, DOM rendering
   Backend: Phase 5 FastAPI on http://localhost:8000
   ===================================================== */

const BASE_URL = '/api';

// ── DOM Elements ─────────────────────────────────────
const locationSelect    = document.getElementById('location');
const cuisineSelect     = document.getElementById('cuisine');
const minRatingSlider   = document.getElementById('min_rating');
const maxPriceSlider    = document.getElementById('max_price');
const ratingVal         = document.getElementById('rating-val');
const priceVal          = document.getElementById('price-val');
const form              = document.getElementById('recommendation-form');
const submitBtn         = document.getElementById('submit-btn');
const btnText           = document.querySelector('.btn-text');
const btnLoader         = document.getElementById('btn-loader');
const errorMsg          = document.getElementById('error-message');
const resultsContainer  = document.getElementById('results-container');
const resultsSection    = document.querySelector('.results-section');
const container         = document.querySelector('.container');

// ── State Helpers ─────────────────────────────────────
let metadataLoaded = false;  // guard so we don't submit before metadata arrives

/** Set a select to a loading skeleton state. */
function setSelectLoading(select, label) {
  select.innerHTML = `<option value="" disabled selected>⏳ Loading ${label}...</option>`;
  select.disabled = true;
}

/** Set a select to an error state. */
function setSelectError(select, label) {
  select.innerHTML = `<option value="" disabled selected>⚠️ Error loading ${label} – is the backend running?</option>`;
  select.disabled = true;
}

/** Populate a select with sorted option values. */
function populateSelect(select, values, placeholder) {
  select.innerHTML = `<option value="" disabled selected>${placeholder}</option>`;
  values.forEach(val => {
    const opt = document.createElement('option');
    opt.value = val;
    opt.textContent = val;
    select.appendChild(opt);
  });
  select.disabled = false;
}

// ── Slider Live Display ───────────────────────────────
minRatingSlider.addEventListener('input', e => { ratingVal.textContent = parseFloat(e.target.value).toFixed(1); });
maxPriceSlider.addEventListener('input',  e => { priceVal.textContent  = parseInt(e.target.value); });

// ── Fallback data (used when backend is unreachable) ──────────────────────
const FALLBACK_LOCATIONS = ['Indiranagar', 'Koramangala', 'HSR', 'Whitefield', 'Jayanagar', 'JP Nagar', 'MG Road'];
const FALLBACK_CUISINES  = ['Biryani', 'Cafe', 'Chinese', 'Desserts', 'Fast Food', 'Italian',
                             'North Indian', 'South Indian', 'Street Food'];

// ── Metadata Fetch (with retry + countdown) ───────────────────────────────
const MAX_RETRIES    = 5;
const RETRY_DELAY_MS = 3000;

async function fetchMetadata() {
  setSelectLoading(locationSelect, 'localities');
  setSelectLoading(cuisineSelect, 'cuisines');

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 6000);

      const response = await fetch(`${BASE_URL}/metadata`, { signal: controller.signal });
      clearTimeout(timeout);

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();

      populateSelect(locationSelect, data.locations && data.locations.length ? data.locations : FALLBACK_LOCATIONS, '📍 Select a locality');
      populateSelect(cuisineSelect,  data.cuisines  && data.cuisines.length  ? data.cuisines  : FALLBACK_CUISINES,  '🍽️ Select a cuisine');
      metadataLoaded = true;
      hideBannerError();
      return; // success — exit immediately

    } catch (err) {
      const isLast = attempt === MAX_RETRIES;
      console.warn(`[fetchMetadata] Attempt ${attempt}/${MAX_RETRIES} failed:`, err.message);

      if (isLast) {
        // All retries exhausted — use fallback data so the UI isn't broken
        console.warn('[fetchMetadata] Backend unreachable. Using fallback data.');
        populateSelect(locationSelect, FALLBACK_LOCATIONS, '📍 Select a locality (offline)');
        populateSelect(cuisineSelect,  FALLBACK_CUISINES,  '🍽️ Select a cuisine (offline)');
        metadataLoaded = true;
        showBannerError('⚠️ Backend server is not running. Showing default options. Start it with start.bat for live data.');
      } else {
        // Show countdown in the dropdown while waiting
        const waitSec = Math.round(RETRY_DELAY_MS / 1000);
        locationSelect.innerHTML = `<option value="" disabled selected>⏳ Retrying (${attempt}/${MAX_RETRIES}) in ${waitSec}s…</option>`;
        cuisineSelect.innerHTML  = `<option value="" disabled selected>⏳ Retrying (${attempt}/${MAX_RETRIES}) in ${waitSec}s…</option>`;
        await new Promise(res => setTimeout(res, RETRY_DELAY_MS));
      }
    }
  }
}


// ── Form Submit Handler ───────────────────────────────
async function fetchRecommendations(e) {
  e.preventDefault();
  hideBannerError();

  // Form validation
  if (!locationSelect.value) {
    showBannerError('Please select a location before searching.');
    locationSelect.focus();
    return;
  }
  if (!cuisineSelect.value) {
    showBannerError('Please select a cuisine before searching.');
    cuisineSelect.focus();
    return;
  }

  setSubmitLoading(true);
  
  // Toggle visibility and layout
  container.classList.add('show-results');
  resultsSection.classList.remove('hidden');

  setResultsLoading();

  const payload = {
    location: locationSelect.value,
    cuisine: cuisineSelect.value,
    min_rating: parseFloat(minRatingSlider.value),
    max_price:  parseFloat(maxPriceSlider.value),
    optional_preferences: document.getElementById('optional_preferences').value.trim() || null
  };

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000); // 30 s for LLM calls

    const response = await fetch(`${BASE_URL}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    clearTimeout(timeout);

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned ${response.status}`);
    }

    const data = await response.json();
    renderResults(data.restaurants, data.message);

  } catch (err) {
    const isTimeout = err.name === 'AbortError';
    const msg = isTimeout
      ? 'The request timed out (LLM took too long). Try again or remove optional preferences.'
      : err.message;

    console.error('[fetchRecommendations] Error:', msg);
    showBannerError(msg);
    setResultsError(msg);

  } finally {
    setSubmitLoading(false);
  }
}

// ── Results Rendering ─────────────────────────────────
function renderResults(restaurants, message) {
  resultsContainer.innerHTML = '';

  if (!restaurants || restaurants.length === 0) {
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🍽️</div>
        <h3>No Matches Found</h3>
        <p>${message || 'Even the finest chefs sometimes come up short. Try adjusting your preferences.'}</p>
      </div>`;
    return;
  }

  restaurants.forEach((rest, index) => {
    const card = document.createElement('div');
    card.className = 'restaurant-card';
    card.style.animationDelay = `${index * 0.1}s`;

    // Safely format values
    const name    = rest.Name    || rest.name || "Unknown Restaurant";
    const loc     = rest.Location || rest.location || "N/A";
    const rating  = rest.Rating   || rest.rating || "N/A";
    const cost    = rest.Approx_cost || rest.cost    || 'N/A';
    const cuisine = rest.Cuisines || rest.cuisine || "Various";
    
    // Natural structured explanation
    const explanation = rest.vibe_explanation || "No explanation provided.";

    card.innerHTML = `
      <div class="card-content">
        <div class="card-header">
          <h3 class="rest-name">${name}</h3>
          <div class="rating-badge">★ ${typeof rating === 'number' ? rating.toFixed(1) : rating}</div>
        </div>

        <div class="rest-tags" style="margin-bottom: 1.5rem;">
          <span class="tag">📍 ${loc}</span>
          <span class="tag">🍽️ ${cuisine}</span>
          <span class="tag">💰 ₹${cost}</span>
        </div>
        
        <div class="ai-reasoning" style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 1.5rem;">
          <span class="ai-reasoning-label">WHY IT MATCHES YOUR VIBE</span>
          <p style="margin-top: 0.5rem; color: #d1d5db; line-height: 1.6; font-style: normal;">${explanation}</p>
        </div>
      </div>
    `;

    resultsContainer.appendChild(card);
  });
}

// ── UI State Helpers ──────────────────────────────────
function setSubmitLoading(isLoading) {
  submitBtn.disabled = isLoading;
  btnText.classList.toggle('hidden', isLoading);
  btnLoader.classList.toggle('hidden', !isLoading);
}

function setResultsLoading() {
  resultsContainer.innerHTML = `
    <div class="empty-state">
      <div class="loader" style="margin: 0 auto; width: 44px; height: 44px; border-width: 4px;"></div>
      <h3 style="margin-top: 1.2rem">AI is curating your list…</h3>
      <p>Groq LLM is analysing your preferences</p>
    </div>`;
}

function setResultsError(msg) {
  resultsContainer.innerHTML = `
    <div class="empty-state" style="border-color: #f87171;">
      <div class="empty-icon">⚠️</div>
      <h3 style="color:#f87171">Something went wrong</h3>
      <p>${msg}</p>
    </div>`;
}

function showBannerError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove('hidden');
}

function hideBannerError() {
  errorMsg.textContent = '';
  errorMsg.classList.add('hidden');
}

// ── Bootstrap ─────────────────────────────────────────
form.addEventListener('submit', fetchRecommendations);
fetchMetadata();
