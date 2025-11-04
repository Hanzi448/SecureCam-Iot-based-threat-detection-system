// static/js/add_criminal.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("criminalForm");
  const preview = document.getElementById("preview");
  const images = document.getElementById("images");
  const status = document.getElementById("status");

  images?.addEventListener("change", () => {
    preview.innerHTML = "";
    Array.from(images.files).slice(0,3).forEach(f=>{
      const url = URL.createObjectURL(f);
      const img = document.createElement("img");
      img.src = url;
      img.style.maxWidth = "120px";
      img.style.marginRight = "8px";
      preview.appendChild(img);
    });
  });

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.textContent = "Uploading...";
    const fd = new FormData(form);
    try {
      const res = await fetch("/api/watchlist/add", { method: "POST", body: fd });
      const data = await res.json();
      if(res.ok){
        status.textContent = `Added: ${data.name} (id=${data.id})`;
        form.reset(); preview.innerHTML = "";
      } else {
        status.textContent = `Error: ${data.error || JSON.stringify(data)}`;
      }
    } catch(err){
      status.textContent = "Upload failed: "+err.message;
    }
  });
});
