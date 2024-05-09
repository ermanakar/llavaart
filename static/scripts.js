document.addEventListener('DOMContentLoaded', function() {
    const imageForm = document.getElementById('image-form');
    const statusMessage = document.getElementById('status-message');
    const submitButton = document.getElementById('submit-button');

    imageForm.addEventListener('submit', handleFormSubmit);

    async function handleFormSubmit(event) {
        event.preventDefault();
        const formData = new FormData(this);

        updateStatusMessage('Uploading image and processing..');
        submitButton.classList.add('loading');

        try {
            const response = await fetch('/', { method: 'POST', body: formData });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            updateStatusMessage('Processing complete. Check results.');
        } catch (error) {
            console.error('Error:', error);
            updateStatusMessage('An error occurred. Please try again.');
        } finally {
            submitButton.classList.remove('loading');
        }
    }

    function updateStatusMessage(message) {
        statusMessage.textContent = message;
    }
});
