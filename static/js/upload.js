document.addEventListener("DOMContentLoaded", () => {
    const dropZoneElement = document.getElementById("drop-zone");
    const inputElement = document.getElementById("file-input");
    const startBtn = document.getElementById("start-btn");
    const fileInfo = document.getElementById("file-info");
    const fileNameDisplay = document.getElementById("file-name");
    const uploadForm = document.getElementById("upload-form");
    const loadingState = document.getElementById("loading-state");
    const loadingText = document.getElementById("loading-text");
    const errorMessage = document.getElementById("error-message");
    
    // Splash Screen Logic
    const splash = document.getElementById("splash-screen");
    const introSection = document.getElementById("intro-section");
    
    if (splash && introSection) {
        setTimeout(() => {
            splash.style.opacity = '0';
            splash.style.visibility = 'hidden';
            setTimeout(() => {
                introSection.style.display = 'block';
            }, 800);
        }, 2000);
    } else {
        if(introSection) introSection.style.display = 'block';
    }

    dropZoneElement.addEventListener("click", (e) => {
        inputElement.click();
    });

    inputElement.addEventListener("change", (e) => {
        if (inputElement.files.length) {
            updateThumbnail(dropZoneElement, inputElement.files[0]);
        }
    });

    dropZoneElement.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZoneElement.classList.add("drop-zone--over");
    });

    ["dragleave", "dragend"].forEach((type) => {
        dropZoneElement.addEventListener(type, (e) => {
            dropZoneElement.classList.remove("drop-zone--over");
        });
    });

    dropZoneElement.addEventListener("drop", (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) {
            inputElement.files = e.dataTransfer.files;
            updateThumbnail(dropZoneElement, e.dataTransfer.files[0]);
        }
        dropZoneElement.classList.remove("drop-zone--over");
    });

    function updateThumbnail(dropZoneElement, file) {
        if (file.type !== "application/pdf") {
            showError("Please upload a valid PDF file.");
            inputElement.value = "";
            fileInfo.style.display = "none";
            startBtn.disabled = true;
            return;
        }
        hideError();
        fileNameDisplay.textContent = file.name;
        fileInfo.style.display = "block";
        startBtn.disabled = false;
    }

    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        if (!inputElement.files.length) {
            showError("Please select a file first.");
            return;
        }

        const formData = new FormData();
        formData.append("resume", inputElement.files[0]);

        // Show loading state
        startBtn.disabled = true;
        dropZoneElement.style.pointerEvents = "none";
        loadingState.style.display = "block";
        hideError();

        try {
            const response = await fetch('/api/resume/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Upload failed');
            }

            loadingText.textContent = "Generating personalized questions...";
            
            // Redirect to interview page with session_id
            window.location.href = `/interview?session_id=${data.session_id}`;
            
        } catch (error) {
            showError(error.message);
            startBtn.disabled = false;
            dropZoneElement.style.pointerEvents = "auto";
            loadingState.style.display = "none";
        }
    });

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.style.display = "block";
    }

    function hideError() {
        errorMessage.style.display = "none";
    }
});
