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
    const evaluationScreen = document.getElementById('evaluation-screen');
    
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
        evaluationScreen.style.display = 'none';
        
        const res = await fetch(`/api/interview/question/${sessionId}`);
        const data = await res.json();

        if (data.status === "completed") {
            window.location.href = `/report?session_id=${sessionId}`;
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
        if (!audioBlob) return;
        
        const submitBtn = document.getElementById('submit-answer-btn');
        submitBtn.disabled = true;
        
        interviewScreen.style.display = 'none';
        loadingMessage.textContent = 'Transcribing your answer...';
        loadingScreen.style.display = 'block';

        try {
            // 1. Transcribe
            const formData = new FormData();
            formData.append('audio', audioBlob, 'answer.webm');
            
            const transRes = await fetch('/api/interview/transcribe', {
                method: 'POST',
                body: formData
            });
            const transData = await transRes.json();
            
            if (!transRes.ok) throw new Error(transData.error || "Transcription failed");
            
            const transcript = transData.transcript;

            // 2. Evaluate
            loadingMessage.textContent = 'Evaluating your answer...';
            
            const evalRes = await fetch('/api/interview/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    question: currentQuestionData.question.question,
                    answer: transcript
                })
            });
            
            const evalData = await evalRes.json();
            if (!evalRes.ok) throw new Error(evalData.error || "Evaluation failed");
            
            showEvaluation(transcript, evalData);
            
        } catch (err) {
            console.error(err);
            alert("Error processing answer: " + err.message);
            loadingScreen.style.display = 'none';
            interviewScreen.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
        }
    });

    function showEvaluation(transcript, evalData) {
        loadingScreen.style.display = 'none';
        evaluationScreen.style.display = 'block';
        
        // Re-trigger animation
        evaluationScreen.classList.remove('slide-up');
        void evaluationScreen.offsetWidth;
        evaluationScreen.classList.add('slide-up');
        
        // Update Progress
        const percent = (currentQuestionData.current_index / currentQuestionData.total) * 100;
        document.getElementById('eval-progress').style.width = `${percent}%`;
        
        document.getElementById('eval-score').textContent = evalData.score;
        document.getElementById('eval-rating').textContent = evalData.rating;
        document.getElementById('eval-transcript').textContent = `"${transcript}"`;
        document.getElementById('eval-feedback').textContent = evalData.feedback;
        document.getElementById('eval-suggested').textContent = evalData.suggested_answer;
        
        const strengthsList = document.getElementById('eval-strengths');
        strengthsList.innerHTML = '';
        (evalData.strengths || []).forEach(s => {
            const li = document.createElement('li');
            li.textContent = s;
            strengthsList.appendChild(li);
        });
        
        const imprList = document.getElementById('eval-improvements');
        imprList.innerHTML = '';
        (evalData.improvements || []).forEach(i => {
            const li = document.createElement('li');
            li.textContent = i;
            imprList.appendChild(li);
        });
    }

    // Handle Next Question
    document.getElementById('next-question-btn').addEventListener('click', async () => {
        const btn = document.getElementById('next-question-btn');
        btn.disabled = true;
        
        try {
            await fetch('/api/interview/next', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            
            await loadCurrentQuestion();
        } catch (err) {
            console.error(err);
            alert("Error loading next question.");
        } finally {
            btn.disabled = false;
        }
    });
});
