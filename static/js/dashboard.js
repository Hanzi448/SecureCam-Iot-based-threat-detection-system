// static/js/dashboard.js
const socket = io();

function svgCheck() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M6 10.2L3.2 7.4L2.2 8.4L6 12.2L14 4.2L13 3.2L6 10.2Z" fill="currentColor"/></svg>`;
}
function svgCross() {
  return `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M4.93 4.93L11.07 11.07M11.07 4.93L4.93 11.07" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>`;
}

socket.on("connect", () => {
  console.log("Socket connected");
});

function createRowFromPayload(data){
  const tr = document.createElement("tr");
  tr.dataset.weapon = data.weapon_detected ? "1" : "0";
  tr.dataset.criminal = data.criminal_detected ? "1" : "0";
  tr.dataset.suspicious = data.suspicious ? "1" : "0";

  // confidence text
  let confText = "—";
  if (data.weapon_conf !== undefined && data.weapon_conf !== null) {
    confText = `<strong>W:</strong> ${Number(data.weapon_conf).toFixed(2)}`;
  } else if (data.confidence !== undefined && data.confidence !== null) {
    confText = `<strong>C:</strong> ${Number(data.confidence).toFixed(2)}`;
  }
  const distText = (data.match_distance !== undefined && data.match_distance !== null)
    ? `<div class="small text-muted">D: ${Number(data.match_distance).toFixed(3)}</div>` : "";

  // image link fallback
  let imageHtml = "N/A";
  if (data.image_url) {
    imageHtml = `<a href="${data.image_url}" target="_blank" class="link-primary">View</a>`;
  } else if (data.local_path) {
    const localName = data.local_path.split('/').pop().split('\\').pop();
    imageHtml = `<span title="${data.local_path}">${localName}</span>`;
  }

  const weaponIcon = data.weapon_detected ? `<span class="icon-true" title="Weapon detected">${svgCheck()}</span>` : `<span class="icon-false" title="No weapon">${svgCross()}</span>`;
  const criminalIcon = data.criminal_detected ? `<span class="icon-true" title="Criminal matched">${svgCheck()}</span>` : `<span class="icon-false" title="Not matched">${svgCross()}</span>`;
  const suspiciousIcon = data.suspicious ? `<span class="icon-true" title="Suspicious">${svgCheck()}</span>` : `<span class="icon-false" title="Not suspicious">${svgCross()}</span>`;
  const alertIcon = data.alert_sent ? `<span class="icon-true" title="Alert sent">${svgCheck()}</span>` : `<span class="icon-false" title="No alert">${svgCross()}</span>`;

  tr.innerHTML = `
    <td>${data.id || ""}</td>
    <td>${data.timestamp || ""}</td>
    <td class="text-center">${weaponIcon}</td>
    <td class="text-center">${criminalIcon}</td>
    <td class="text-center">${suspiciousIcon}</td>
    <td>${confText}${distText}</td>
    <td>${data.criminal_name || "—"}</td>
    <td>${imageHtml}</td>
    <td class="text-center">${alertIcon}</td>
  `;

  return tr;
}

socket.on("new_event", (data) => {
  try {
    const tbody = document.getElementById("eventsBody");
    if(!tbody) return;

    const filter = document.getElementById("filterType")?.value || "all";
    if(filter !== "all"){
      if(filter === "weapon" && !data.weapon_detected) return;
      if(filter === "criminal" && !data.criminal_detected) return;
      if(filter === "suspicious" && !data.suspicious) return;
    }

    const tr = createRowFromPayload(data);
    tbody.insertBefore(tr, tbody.firstChild);

    // update counters
    const totalEl = document.getElementById("stat_total");
    totalEl.textContent = (parseInt(totalEl.textContent || "0", 10) + 1).toString();

    if(data.weapon_detected){
      const el = document.getElementById("stat_weapons");
      el.textContent = (parseInt(el.textContent || "0", 10) + 1).toString();
    }
    if(data.criminal_detected){
      const el = document.getElementById("stat_criminals");
      el.textContent = (parseInt(el.textContent || "0", 10) + 1).toString();
    }
    if(data.suspicious){
      const el = document.getElementById("stat_suspicious");
      el.textContent = (parseInt(el.textContent || "0", 10) + 1).toString();
    }

  } catch(e){
    console.error("new_event handler error:", e);
  }
});

// filter + clear
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("filterType")?.addEventListener("change", () => {
    location.reload();
  });
  document.getElementById("clearTable")?.addEventListener("click", () => {
    const tbody = document.getElementById("eventsBody"); if(tbody) tbody.innerHTML = "";
    ["stat_total","stat_weapons","stat_criminals","stat_suspicious"].forEach(id=>document.getElementById(id).textContent="0");
  });
});
