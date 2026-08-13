let mediaRecorder;
let audioChunks = [];
let audioBlob = null;
let stream = null;
let recordingInterval;
let startTime;

const startRecordBtn = document.getElementById('start-record-btn');
const stopRecordBtn = document.getElementById('stop-record-btn');
const recordingStatus = document.getElementById('recording-status');
const recordingTimer = document.getElementById('recording-timer');
const playbackContainer = document.getElementById('audio-playback-container');
const audioPlayback = document.getElementById('audio-playback');
const reRecordBtn = document.getElementById('re-record-btn');
const submitAnswerBtn = document.getElementById('submit-answer-btn');

async function initRecorder() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
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

    startRecordBtn.style.display = 'none';
    stopRecordBtn.style.display = 'inline-block';
    recordingStatus.style.display = 'block';
    playbackContainer.style.display = 'none';
});

stopRecordBtn.addEventListener('click', () => {
    mediaRecorder.stop();
    clearInterval(recordingInterval);
    
    stopRecordBtn.style.display = 'none';
    startRecordBtn.style.display = 'none'; // hide start as well until re-record
});

reRecordBtn.addEventListener('click', () => {
    audioBlob = null;
    audioPlayback.src = '';
    playbackContainer.style.display = 'none';
    startRecordBtn.style.display = 'inline-block';
});
