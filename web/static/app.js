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

async function loadPredictions(city) {
    const response = await fetch(`${CONFIG.API_BASE_URL}/predictions/${city}`);
    const predictions = await response.json();
    console.log(predictions);

    const predictionsDiv = document.getElementById('predictions');
    predictionsDiv.innerHTML = '';

    predictions.forEach(prediction => {
        const box = document.createElement('div');
        console.log(prediction.horizon, prediction.predicted_aqi)
        box.textContent = `${prediction.horizon}h:\t${prediction.predicted_aqi}`

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
document.addEventListener('DOMContentLoaded', loadCities);

// When city is selected
document.getElementById('city-select').addEventListener('change', (event) => {
    const city = event.target.value;
    if (city) {
        loadPredictions(city);
    }
})