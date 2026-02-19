// Strike7 Data Portal - Client Application
// Version 1.0.0

const API_KEY = "EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL";

const API_BASE_URL = window.location.origin;

/**
 * Fetch secret data from the protected API endpoint
 */
function fetchSecretData() {
    const resultDiv = document.getElementById('result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Loading secret data...</p>';

    fetch(`${API_BASE_URL}/api/secret`, {
        method: 'GET',
        headers: {
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultDiv.className = 'error';
            resultDiv.innerHTML = `<strong>Error:</strong> ${data.error}`;
        } else {
            resultDiv.className = 'success';
            resultDiv.innerHTML = `
                <h3>Secret Data Retrieved!</h3>
                <p><strong>Message:</strong> ${data.message}</p>
                <p><strong>Flag:</strong> <code>${data.flag}</code></p>
                <p><strong>Secret Data:</strong></p>
                <pre>${JSON.stringify(data.secret_data, null, 2)}</pre>
            `;
        }
    })
    .catch(error => {
        resultDiv.className = 'error';
        resultDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
    });
}

/**
 * Fetch public data (no authentication required)
 */
function showPublicData() {
    const resultDiv = document.getElementById('result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Loading public data...</p>';

    fetch(`${API_BASE_URL}/api/public`)
        .then(response => response.json())
        .then(data => {
            resultDiv.className = 'success';
            resultDiv.innerHTML = `
                <h3>Public Data</h3>
                <p>${data.message}</p>
                <pre>${JSON.stringify(data.data, null, 2)}</pre>
            `;
        })
        .catch(error => {
            resultDiv.className = 'error';
            resultDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
        });
}

// Application initialization
console.log("Strike7 Data Portal initialized");
console.log("API Base URL:", API_BASE_URL);
