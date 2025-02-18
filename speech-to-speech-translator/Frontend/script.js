let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const startButton = document.getElementById("startBtn");
const stopButton = document.getElementById("stopBtn");
const recordingIndicator = document.getElementById("recordingIndicator");
const detectedText = document.getElementById("detectedText");
const translatedText = document.getElementById("translatedText");
const speakIn = document.getElementById("speak-in");
const translateTo = document.getElementById("translate-to");
const audioPlayer = document.getElementById("audioPlayer");

// Event Listeners
startButton.addEventListener("click", () => {
    console.log("Start Recording Clicked!");
    startRecording();
});

stopButton.addEventListener("click", () => {
    console.log("Stop Recording Clicked!");
    stopRecording();
});

// Start recording function
async function startRecording() {
    console.log("Attempting to start recording...");
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        console.log("Recording started...");

        // Update UI elements
        startButton.disabled = true;
        stopButton.disabled = false;
        recordingIndicator.style.display = "block";

        mediaRecorder.onstart = () => {
            isRecording = true;
        };

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            isRecording = false;
            recordingIndicator.style.display = "none";
            
            // Update UI elements
            startButton.disabled = false;
            stopButton.disabled = true;

            console.log("Recording stopped, processing audio...");

            // Convert recorded audio to blob
            const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
            sendAudioToBackend(audioBlob);
            
            // Clean up media stream
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
    } catch (error) {
        console.error("Error starting recording:", error);
        alert("Error accessing microphone. Please allow mic permissions.");
        
        // Reset UI elements
        startButton.disabled = false;
        stopButton.disabled = true;
        recordingIndicator.style.display = "none";
    }
}

// Stop recording function
function stopRecording() {
    if (mediaRecorder && isRecording) {
        console.log("Stopping recording...");
        mediaRecorder.stop();
    } else {
        console.log("No active recording to stop.");
    }
}

// Send recorded audio to backend
async function sendAudioToBackend(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob);
    formData.append("source_lang", speakIn.value);
    formData.append("target_lang", translateTo.value);

    try {
        console.log("Sending audio to backend...");
        const response = await fetch("http://127.0.0.1:5000/real-time-translate", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        console.log("Backend Response:", result);

        if (result.error) {
            alert("Error: " + result.error);
        } else {
            detectedText.innerText = result.original_text;
            translatedText.innerText = result.translated_text;
            audioPlayer.src = result.audio_url;
            audioPlayer.style.display = "block";
        }
    } catch (error) {
        console.error("Error sending audio:", error);
        alert("Error communicating with the server. Please try again.");
    }
}