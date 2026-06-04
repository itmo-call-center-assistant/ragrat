let audioContext;
let chatHistory = [];
let peerConnection;
let webrtc_id;
let isRecording = false;
import { marked } from "https://unpkg.com/marked@18.0.3/lib/marked.esm.js";

const audioOutput = document.getElementById("audio-output");
const startButton = document.getElementById("start-button");
const chatMessages = document.getElementById("chat-messages");

function updateButtonState() {
  startButton.classList.remove("state-connecting", "state-stop");
  startButton.disabled = false;

  if (peerConnection && peerConnection.connectionState === "connecting") {
    startButton.classList.add("state-connecting");
    startButton.disabled = true;
    isRecording = false;
  } else if (peerConnection && peerConnection.connectionState === "connected") {
    startButton.classList.add("state-stop");
    isRecording = true;
  } else {
    isRecording = false;
  }
}

function showError(message) {
  const toast = document.getElementById("error-toast");
  toast.textContent = message;
  toast.className = "toast error visible";
  setTimeout(() => {
    toast.classList.remove("visible");
  }, 5000);
}

async function setupWebRTC() {
  peerConnection = new RTCPeerConnection();
  updateButtonState();
  const timeoutId = setTimeout(() => {
    const toast = document.getElementById("error-toast");
    toast.textContent =
      "Connection is taking longer than usual. Are you on a VPN?";
    toast.className = "toast warning visible";
    setTimeout(() => {
      toast.classList.remove("visible");
    }, 5000);
  }, 5000);
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContext();
    stream.getTracks().forEach((track) => {
      peerConnection.addTrack(track, stream);
    });
    peerConnection.addEventListener("connectionstatechange", () => {
      console.log("Connection state:", peerConnection.connectionState);
      if (peerConnection.connectionState === "connected") {
        clearTimeout(timeoutId);
        const toast = document.getElementById("error-toast");
        toast.classList.remove("visible");
      }
      updateButtonState();
    });
    peerConnection.addEventListener("track", (evt) => {
      if (audioOutput.srcObject !== evt.streams[0]) {
        audioOutput.srcObject = evt.streams[0];
        audioOutput.play();
      }
    });
    const dataChannel = peerConnection.createDataChannel("text");
    dataChannel.onmessage = (event) => {
      const eventJson = JSON.parse(event.data);
      const typingIndicator = document.getElementById("typing-indicator");
      if (eventJson.type === "error") {
        showError(eventJson.message);
      } else if (eventJson.type === "send_input") {
        fetch("/input_hook", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            webrtc_id: webrtc_id,
            chatbot: chatHistory,
          }),
        });
      } else if (eventJson.type === "log") {
        if (eventJson.data === "pause_detected") {
          typingIndicator.classList.add("visible");
          chatMessages.scrollTop = chatMessages.scrollHeight;
        } else if (eventJson.data === "response_starting") {
          typingIndicator.classList.remove("visible");
        }
      }
    };
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    await new Promise((resolve) => {
      if (peerConnection.iceGatheringState === "complete") {
        resolve();
      } else {
        const checkState = () => {
          if (peerConnection.iceGatheringState === "complete") {
            peerConnection.removeEventListener(
              "icegatheringstatechange",
              checkState,
            );
            resolve();
          }
        };
        peerConnection.addEventListener("icegatheringstatechange", checkState);
      }
    });
    webrtc_id = Math.random().toString(36).substring(7);
    const response = await fetch("/webrtc/offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sdp: peerConnection.localDescription.sdp,
        type: peerConnection.localDescription.type,
        webrtc_id: webrtc_id,
      }),
    });
    const serverResponse = await response.json();
    if (serverResponse.status === "failed") {
      showError(
        serverResponse.meta.error === "concurrency_limit_reached"
          ? `Too many connections. Maximum limit is ${serverResponse.meta.limit}`
          : serverResponse.meta.error,
      );
      stop();
      return;
    }
    await peerConnection.setRemoteDescription(serverResponse);
    const eventSource = new EventSource("/outputs?webrtc_id=" + webrtc_id);
    eventSource.addEventListener("output", (event) => {
      const eventJson = JSON.parse(event.data);
      if (eventJson.role === "retrieved_chunks") {
        displayChunks(eventJson.chunks);
      } else {
        addMessage(eventJson.role, eventJson.content);
      }
    });
  } catch (err) {
    clearTimeout(timeoutId);
    console.error("Error setting up WebRTC:", err);
    showError("Failed to establish connection. Please try again.");
    stop();
  }
}

function addMessage(role, content) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", role);
  if (role === "assistant" && marked) {
    messageDiv.innerHTML = marked.parse(content);
  } else {
    messageDiv.textContent = content;
  }
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  chatHistory.push({ role, content });
}

function displayChunks(chunks) {
  const container = document.createElement("div");
  container.classList.add("chunks-container");
  const header = document.createElement("div");
  header.classList.add("chunks-header");
  header.textContent = `Retrieved Chunks (${chunks.length})`;
  container.appendChild(header);
  chunks.forEach((chunk, i) => {
    const chunkDiv = document.createElement("div");
    chunkDiv.classList.add("chunk-item");
    chunkDiv.innerHTML = `<div class="chunk-text">${escapeHtml(chunk.text)}</div><div class="chunk-doc">${escapeHtml(chunk.document)}</div>`;
    container.appendChild(chunkDiv);
  });
  chatMessages.appendChild(container);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function stop() {
  if (peerConnection) {
    if (peerConnection.getTransceivers) {
      peerConnection.getTransceivers().forEach((transceiver) => {
        if (transceiver.stop) {
          transceiver.stop();
        }
      });
    }
    if (peerConnection.getSenders) {
      peerConnection.getSenders().forEach((sender) => {
        if (sender.track && sender.track.stop) sender.track.stop();
      });
    }
    peerConnection.close();
    peerConnection = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  isRecording = false;
  updateButtonState();
}

startButton.addEventListener("click", () => {
  if (!isRecording) {
    setupWebRTC();
  } else {
    stop();
  }
});
