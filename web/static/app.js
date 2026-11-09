const horizonToModel = {
    2: 'lightgbm_short',
    4: 'lightgbm_medium',
    8: 'lightgbm_medium',
    12: 'lightgbm_medium',
    24: 'lightgbm_long',
    48: 'lightgbm_long',
    
}

let metrics = {};

async function loadCities() {
    const response = await fetch(`${CONFIG.API_BASE_URL}/cities`);
    const data = await response.json();

    const select = document.getElementById('city-select');
    select.innerHTML = ''; // clear "Loading..."

    data.cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        select.appendChild(option);
    });
}

async function loadMetrics() {
    const response = await fetch(`${CONFIG.API_BASE_URL}/metrics`);
    metrics = await response.json();
}

async function loadPredictions(city) {
    const response = await fetch(`${CONFIG.API_BASE_URL}/predictions/${city}`);
    const predictions = await response.json();
    console.log(predictions);

    const date = new Date(predictions[0].collected_at);
    const timeStr = date.toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit'});
    const dateStr = date.toLocaleDateString('en-GB', {weekday: 'short', day: 'numeric', month: 'long', year: 'numeric'});

    const status = document.getElementById('status');
    status.textContent = `Predictions at ${timeStr} on ${dateStr}`

    const predictionsDiv = document.getElementById('predictions');
    predictionsDiv.innerHTML = '';

    predictions.forEach(prediction => {
        const box = document.createElement('div');

        const model = horizonToModel[prediction.horizon];
        const rmse = Math.round(metrics[model].rmse)

        console.log(prediction.horizon, prediction.predicted_aqi)

        const forecastDate = new Date(prediction.forecast_for);
        let forecastStr = ''
        if ([2, 4, 8, 12].includes(prediction.horizon)) {
            forecastStr = forecastDate.toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit'});
        } else {
            forecastStr = forecastDate.toLocaleDateString('en-GB', {weekday: 'short'})
        }

        const timeSpan = document.createElement('span');
        timeSpan.className = 'forecast-time';
        timeSpan.textContent = forecastStr;

        const aqiLine = document.createElement('span');
        aqiLine.className = 'aqi-line';

        const aqiSpan = document.createElement('span');
        aqiSpan.className = 'aqi-value';
        aqiSpan.textContent = prediction.predicted_aqi;

        const rmseSpan = document.createElement('span');
        rmseSpan.className = 'rmse-value';
        rmseSpan.textContent = '\u00B1' + rmse;

        aqiLine.appendChild(aqiSpan);
        aqiLine.appendChild(rmseSpan);

        box.appendChild(timeSpan);
        box.appendChild(aqiLine);

        if (prediction.predicted_aqi <= 50) {
            box.className = 'prediction-box aqi-good';
        } else if (prediction.predicted_aqi <= 100) {
            box.className = 'prediction-box aqi-moderate';
        } else if (prediction.predicted_aqi <= 150) {
            box.className = 'prediction-box aqi-unhealthy-sg';
        } else if (prediction.predicted_aqi <= 200) {
            box.className = 'prediction-box aqi-unhealthy';
        } else if (prediction.predicted_aqi <= 300) {
            box.className = 'prediction-box aqi-v-unhealthy';
        } else {
            box.className = 'prediction-box aqi-hazardous';
        }

        predictionsDiv.appendChild(box)
    })
}

// Run on page load
document.addEventListener('DOMContentLoaded', async () => {
    loadCities();
    await loadMetrics();
    console.log(metrics);
});

// When city is selected
document.getElementById('city-select').addEventListener('change', (event) => {
    const city = event.target.value;
    if (city) {
        loadPredictions(city);
    }
})