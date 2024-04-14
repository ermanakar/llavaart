document.addEventListener('DOMContentLoaded', function() {
    const imageForm = document.getElementById('image-form');
    const statusMessage = document.getElementById('status-message');
    const overallProgress = document.getElementById('overall-progress');
    const resultsSection = document.querySelector('.results-section');
    const iterationCount = document.getElementById('iteration-count');

    imageForm.addEventListener('submit', handleFormSubmit);

    async function handleFormSubmit(event) {
        event.preventDefault();
        const formData = new FormData(this);
        const totalIterations = parseInt(iterationCount.value);
        const submitButton = document.getElementById('submit-button'); // Get the submit button by its ID
    
        clearPreviousResults();
        initializeIterationPlaceholders(totalIterations);
        updateOverallProgress(0);
        updateStatusMessage('Uploading image and processing...');
        submitButton.classList.add('loading'); // Add the loading class to show the spinner
    
        try {
            const response = await fetch('/', { method: 'POST', body: formData });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const reader = response.body.getReader();
            await handleStream(reader, totalIterations);
        } catch (error) {
            console.error('Error:', error);
            updateStatusMessage('An error occurred. Please try again.');
        } finally {
            submitButton.classList.remove('loading'); // Remove the loading class to hide the spinner
        }
    }
    
    async function handleStream(reader, totalIterations) {
        const decoder = new TextDecoder();
        let receivedIterations = 0;
        let { value, done } = await reader.read();
        while (!done) {
            const chunk = decoder.decode(value, { stream: true });
            if (chunk.trim()) {
                try {
                    const json = JSON.parse(chunk);
                    if (json.results) {
                        json.results.forEach(result => {
                            if (result.iteration && result.image_url && result.description) {
                                displayResult(result);
                                receivedIterations++;
                                updateOverallProgress((receivedIterations / totalIterations) * 100);
                            } else {
                                console.error('Received data is missing required properties:', result);
                            }
                        });
                    }
                } catch (e) {
                    console.error('Error parsing JSON:', e);
                    updateStatusMessage('An error occurred during stream processing. Please check the results.');
                    break;
                }
            }
            ({ value, done } = await reader.read());
        }
        finalizeProcessing(receivedIterations, totalIterations);
    }
        
    function initializeIterationPlaceholders(totalIterations) {
        for (let i = 1; i <= totalIterations; i++) {
            const placeholder = document.createElement('div');
            placeholder.classList.add('iteration-placeholder');
            placeholder.setAttribute('data-iteration', i);
            placeholder.innerHTML = `<h3>Iteration ${i}</h3><p>Waiting for results...</p>`;
            resultsSection.appendChild(placeholder);
        }
    }

    function displayResult(data) {
        const placeholder = document.querySelector(`.iteration-placeholder[data-iteration="${data.iteration}"]`);
        if (placeholder) {
            placeholder.innerHTML = `
                <h3>Iteration ${data.iteration}</h3>
                <img src="${data.image_url}" alt="Generated Image ${data.iteration}" class="responsive-image">
                <p>${sanitize(data.description)}</p>
            `;
        } else {
            console.error(`Placeholder for iteration ${data.iteration} not found.`);
            // Handle the error for the user, maybe display a message
            updateStatusMessage(`Could not display results for iteration ${data.iteration}.`);
        }
    }

    function clearPreviousResults() {
        while (resultsSection.firstChild) {
            resultsSection.removeChild(resultsSection.firstChild);
        }
    }

    function updateOverallProgress(percentage) {
        overallProgress.textContent = `Processing: ${percentage.toFixed(0)}% complete`;
    }

    function updateStatusMessage(message) {
        statusMessage.textContent = message;
    }

    function finalizeProcessing(receivedIterations, totalIterations) {
        if (receivedIterations === totalIterations) {
            updateStatusMessage('All iterations processed successfully.');
        } else {
            updateStatusMessage(`Only ${receivedIterations} of ${totalIterations} iterations completed. Check results.`);
        }
    }

    function sanitize(text) {
        const temp = document.createElement('div');
        temp.textContent = text;
        return temp.innerHTML;
    }

    function displayIterationError(iteration, message) {
        const placeholder = document.querySelector(`.iteration-placeholder[data-iteration="${iteration}"]`);
        if (placeholder) {
            placeholder.innerHTML = `<h3>Iteration ${iteration}</h3><p>Error: ${message}</p>`;
        }
    }
    
});
