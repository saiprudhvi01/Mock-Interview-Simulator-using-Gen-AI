let mediaRecorder;
let audioChunks = [];
let audioBlob = null;
let stream = null;
let recordingInterval;
let startTime;
let transcript = '';

const startRecordBtn = document.getElementById('start-record-btn');
const stopRecordBtn = document.getElementById('stop-record-btn');
const recordingStatus = document.getElementById('recording-status');
const recordingTimer = document.getElementById('recording-timer');
const playbackContainer = document.getElementById('audio-playback-container');
const audioPlayback = document.getElementById('audio-playback');
const reRecordBtn = document.getElementById('re-record-btn');
const submitAnswerBtn = document.getElementById('submit-answer-btn');

// Web Speech API for transcription
let recognition = null;

function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcriptText = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcriptText;
                } else {
                    interimTranscript += transcriptText;
                }
            }

            if (finalTranscript) {
                transcript += finalTranscript;
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'not-allowed') {
                alert('Microphone access is required for the interview. Please enable it in your browser settings.');
            }
        };
    } else {
        console.warn('Web Speech API not supported in this browser');
    }
}

async function initRecorder() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        initSpeechRecognition();
    } catch (err) {
        console.error('Error accessing microphone:', err);
        alert('Microphone access is required for the interview. Please enable it in your browser settings.');
    }
}

function updateTimer() {
    const now = Date.now();
    const diff = new Date(now - startTime);
    const m = diff.getMinutes().toString().padStart(2, '0');
    const s = diff.getSeconds().toString().padStart(2, '0');
    recordingTimer.textContent = `${m}:${s}`;
}

startRecordBtn.addEventListener('click', async () => {
    if (!stream) {
        await initRecorder();
        if (!stream) return;
    }

    transcript = '';
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
        audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPlayback.src = audioUrl;
        
        recordingStatus.style.display = 'none';
        playbackContainer.style.display = 'block';
    };

    mediaRecorder.start();
    startTime = Date.now();
    recordingInterval = setInterval(updateTimer, 1000);
    updateTimer();

    // Start speech recognition
    if (recognition) {
        try {
            recognition.start();
        } catch (e) {
            console.error('Speech recognition start error:', e);
        }
    }

    startRecordBtn.style.display = 'none';
    stopRecordBtn.style.display = 'inline-block';
    recordingStatus.style.display = 'block';
    playbackContainer.style.display = 'none';
});

stopRecordBtn.addEventListener('click', () => {
    mediaRecorder.stop();
    clearInterval(recordingInterval);
    
    // Stop speech recognition
    if (recognition) {
        try {
            recognition.stop();
        } catch (e) {
            console.error('Speech recognition stop error:', e);
        }
    }
    
    stopRecordBtn.style.display = 'none';
    startRecordBtn.style.display = 'none'; // hide start as well until re-record
});

reRecordBtn.addEventListener('click', () => {
    audioBlob = null;
    audioPlayback.src = '';
    transcript = '';
    playbackContainer.style.display = 'none';
    startRecordBtn.style.display = 'inline-block';
});
