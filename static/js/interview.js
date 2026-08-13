document.addEventListener("DOMContentLoaded", async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (!sessionId) {
        window.location.href = '/';
        return;
    }

    const loadingScreen = document.getElementById('loading-screen');
    const loadingMessage = document.getElementById('loading-message');
    const interviewScreen = document.getElementById('interview-screen');
    
    const questionCounter = document.getElementById('question-counter');
    const questionCategory = document.getElementById('question-category');
    const questionText = document.getElementById('question-text');
    
    let currentQuestionData = null;

    // Initial setup: Generate questions
    try {
        loadingScreen.style.display = 'block';
        
        const genRes = await fetch('/api/interview/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        if (!genRes.ok) throw new Error("Failed to generate questions");
        
        await loadCurrentQuestion();
    } catch (err) {
        console.error(err);
        alert("Error initializing interview session.");
        window.location.href = '/';
    }

    async function loadCurrentQuestion() {
        loadingScreen.style.display = 'none';
        
        const res = await fetch(`/api/interview/question/${sessionId}`);
        const data = await res.json();

        if (data.status === "completed") {
            // All questions done, trigger batch evaluation
            await performBatchEvaluation();
            return;
        }

        currentQuestionData = data;
        
        // Update Progress
        const percent = ((data.current_index - 1) / data.total) * 100;
        document.getElementById('interview-progress').style.width = `${percent}%`;
        
        questionCounter.textContent = `Question ${data.current_index} of ${data.total}`;
        
        // Handle Badge
        const cat = data.question.category.toLowerCase();
        questionCategory.textContent = data.question.category;
        questionCategory.className = 'badge';
        if(cat.includes('hr') || cat.includes('behavioral')) {
            questionCategory.classList.add('hr');
        } else {
            questionCategory.classList.add('tech');
        }
        
        questionText.textContent = data.question.question;
        
        // Reset recorder UI
        document.getElementById('re-record-btn').click(); 
        
        interviewScreen.style.display = 'block';
        
        // Re-trigger animation
        interviewScreen.classList.remove('fade-in');
        void interviewScreen.offsetWidth;
        interviewScreen.classList.add('fade-in');
    }

    // Handle Answer Submission
    document.getElementById('submit-answer-btn').addEventListener('click', async () => {
        if (!audioBlob && !transcript) return;
        
        const submitBtn = document.getElementById('submit-answer-btn');
        submitBtn.disabled = true;
        
        interviewScreen.style.display = 'none';
        loadingMessage.textContent = 'Saving your answer...';
        loadingScreen.style.display = 'block';

        try {
            // Use transcript from Web Speech API, fallback to empty string if not available
            const answerText = transcript || '';
            
            // Submit answer without evaluation
            const submitRes = await fetch('/api/interview/submit_answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    answer: answerText
                })
            });
            
            const submitData = await submitRes.json();
            if (!submitRes.ok) throw new Error(submitData.error || "Failed to submit answer");
            
            // Move to next question
            await fetch('/api/interview/next', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            
            // Load next question or proceed to batch evaluation
            await loadCurrentQuestion();
            
        } catch (err) {
            console.error(err);
            alert("Error processing answer: " + err.message);
            loadingScreen.style.display = 'none';
            interviewScreen.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
        }
    });

    async function performBatchEvaluation() {
        loadingMessage.textContent = 'Evaluating all your answers...';
        loadingScreen.style.display = 'block';
        
        try {
            const evalRes = await fetch('/api/interview/evaluate_batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            
            const evalData = await evalRes.json();
            if (!evalRes.ok) throw new Error(evalData.error || "Batch evaluation failed");
            
            // Redirect to report page
            window.location.href = `/report?session_id=${sessionId}`;
            
        } catch (err) {
            console.error(err);
            alert("Error during evaluation: " + err.message);
            loadingMessage.textContent = 'Evaluation failed. Click to retry.';
            
            // Add retry functionality
            loadingScreen.onclick = async () => {
                loadingScreen.onclick = null;
                await performBatchEvaluation();
            };
        }
    }
});
