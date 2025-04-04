document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers
    flatpickr("#start-date", {
        dateFormat: "d/m/Y",
        minDate: "today",
        allowInput: true
    });
    
    flatpickr("#end-date", {
        dateFormat: "d/m/Y",
        minDate: "today",
        allowInput: true
    });
    
    // Handle form submission
    const scraperForm = document.getElementById('scraper-form');
    const runButton = document.getElementById('run-btn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    const progressBar = document.getElementById('progress-bar');
    const progressStatus = document.getElementById('progress-status');
    
    scraperForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get date values
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        // Validate inputs
        if (!startDate || !endDate) {
            showError('Please select both start and end dates.');
            return;
        }
        
        // Parse dates for comparison
        const startDateObj = parseDate(startDate);
        const endDateObj = parseDate(endDate);
        
        if (!startDateObj || !endDateObj) {
            showError('Invalid date format. Please use DD/MM/YYYY format.');
            return;
        }
        
        if (startDateObj > endDateObj) {
            showError('End date must be after or equal to start date.');
            return;
        }
        
        // Calculate date difference for progress bar
        const dateDiff = Math.ceil((endDateObj - startDateObj) / (1000 * 60 * 60 * 24)) + 1;
        
        // Show loading indicator
        runButton.disabled = true;
        hideError();
        loadingIndicator.classList.remove('d-none');
        
        // Update progress status
        progressStatus.textContent = 'Starting scraper...';
        simulateProgress(dateDiff);
        
        // Call the scraping API
        fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate
            })
        })
        .then(response => response.json())
        .then(data => {
            // Handle the response
            if (data.error) {
                showError(data.error);
                runButton.disabled = false;
                loadingIndicator.classList.add('d-none');
            } else {
                // Success - redirect to results page
                progressBar.style.width = '100%';
                progressStatus.textContent = 'Scraping completed! Redirecting to results...';
                setTimeout(() => {
                    window.location.href = '/results';
                }, 1000);
            }
        })
        .catch(error => {
            showError('An error occurred during the scraping process: ' + error.message);
            runButton.disabled = false;
            loadingIndicator.classList.add('d-none');
        });
    });
    
    // Helper function to parse date string (DD/MM/YYYY)
    function parseDate(dateStr) {
        const parts = dateStr.split('/');
        if (parts.length !== 3) return null;
        
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1; // JS months are 0-indexed
        const year = parseInt(parts[2], 10);
        
        return new Date(year, month, day);
    }
    
    // Helper function to show error message
    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.classList.remove('d-none');
    }
    
    // Helper function to hide error message
    function hideError() {
        errorContainer.classList.add('d-none');
    }
    
    // Helper function to simulate progress updates
    function simulateProgress(totalDays) {
        let progress = 0;
        const increment = 100 / (totalDays * 2); // Each day has multiple steps
        
        const updateProgress = () => {
            progress += increment;
            if (progress > 95) return; // Don't reach 100% until actually complete
            
            progressBar.style.width = progress + '%';
            
            // Update status message
            if (progress < 30) {
                progressStatus.textContent = 'Navigating to Seajets website...';
            } else if (progress < 60) {
                progressStatus.textContent = 'Processing itineraries...';
            } else {
                progressStatus.textContent = 'Collecting seat availability data...';
            }
            
            setTimeout(updateProgress, (30000 / totalDays)); // Spread updates over a reasonable time
        };
        
        updateProgress();
    }
});
