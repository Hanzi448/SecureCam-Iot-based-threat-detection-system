// static/js/home.js

async function api(path, method = "GET") {
  try {
    const res = await fetch(path, { method });
    return await res.json();
  } catch (e) {
    console.error(`API ${method} ${path} failed:`, e);
    return {};
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btnStart = document.getElementById("btnStart");
  const btnStop = document.getElementById("btnStop");
  const liveImg = document.getElementById("liveImg");
  const statusText = document.getElementById("statusText");

  // ------------------------------
  // Update camera status + UI
  // ------------------------------
  async function refreshStatus() {
    try {
      const st = await api("/api/camera/status");
      if (st.running) {
        btnStart.disabled = true;
        btnStop.disabled = false;
        statusText.textContent = "Status: Running";
        statusText.className = "badge bg-success";
        liveImg.src = "/api/camera/video_feed?ts=" + Date.now(); // ensure refresh
      } else {
        btnStart.disabled = false;
        btnStop.disabled = true;
        statusText.textContent = "Status: Stopped";
        statusText.className = "badge bg-danger";
        liveImg.src = "";
      }
    } catch (e) {
      console.error("Status update failed:", e);
      statusText.textContent = "Status: Error";
      statusText.className = "badge bg-warning text-dark";
    }
  }

  // ------------------------------
  // Start / Stop button handlers
  // ------------------------------
  btnStart.addEventListener("click", async () => {
    btnStart.disabled = true;
    statusText.textContent = "Status: Starting...";
    statusText.className = "badge bg-info text-dark";

    try {
      await api("/api/camera/start", "POST");
      console.log("Camera started");
    } catch (e) {
      alert("Failed to start camera.");
      console.error(e);
    }
    setTimeout(refreshStatus, 800);
  });

  btnStop.addEventListener("click", async () => {
    btnStop.disabled = true;
    statusText.textContent = "Status: Stopping...";
    statusText.className = "badge bg-secondary";

    try {
      await api("/api/camera/stop", "POST");
      console.log("Camera stopped");
    } catch (e) {
      alert("Failed to stop camera.");
      console.error(e);
    }
    setTimeout(refreshStatus, 800);
  });

  // ------------------------------
  // Auto-refresh status
  // ------------------------------
  refreshStatus();
  setInterval(refreshStatus, 4000);
});
