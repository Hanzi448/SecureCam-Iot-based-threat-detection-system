// static/js/home.js
async function api(path, method='GET') {
  const res = await fetch(path, {method});
  return res.json();
}

document.addEventListener("DOMContentLoaded", async () => {
  const btnStart = document.getElementById("btnStart");
  const btnStop = document.getElementById("btnStop");
  const openWindow = document.getElementById("openWindow");

  async function refreshStatus() {
    try {
      const st = await api("/api/camera/status");
      if (st.running) {
        btnStart.disabled = true;
        btnStop.disabled = false;
      } else {
        btnStart.disabled = false;
        btnStop.disabled = true;
      }
    } catch (e) {
      console.error("status fail", e);
    }
  }

  btnStart.addEventListener("click", async () => {
    btnStart.disabled = true;
    try {
      await api("/api/camera/start", "POST");
    } catch (e) {
      console.error(e);
      alert("Failed to start camera.");
    }
    setTimeout(refreshStatus, 500);
  });

  btnStop.addEventListener("click", async () => {
    btnStop.disabled = true;
    try {
      await api("/api/camera/stop", "POST");
    } catch (e) {
      console.error(e);
      alert("Failed to stop camera.");
    }
    setTimeout(refreshStatus, 500);
  });

  openWindow.addEventListener("click", () => {
    window.open("/live", "smart_live", "width=900,height=700");
  });

  // poll status every 3s
  refreshStatus();
  setInterval(refreshStatus, 3000);
});
