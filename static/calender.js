// static/calendar.js
async function loadAttendance() {
  const res = await fetch("/api/attendance");
  const data = await res.json();
  const calendar = document.getElementById("calendar");
  calendar.innerHTML = "";

  const today = new Date();
  const dates = Object.keys(data).sort().reverse();

  dates.forEach(dateStr => {
    const dayDiv = document.createElement("div");
    dayDiv.className = "day";

    const dateObj = new Date(dateStr);
    const options = { weekday: 'short', month: 'short', day: 'numeric' };
    const formatted = dateObj.toLocaleDateString(undefined, options);

    const dateEl = document.createElement("div");
    dateEl.className = "date";
    dateEl.textContent = formatted;
    dayDiv.appendChild(dateEl);

    data[dateStr].forEach(entry => {
      const statusEl = document.createElement("div");
      const status = entry.status.toLowerCase();

      statusEl.className = "status " + (
        status.includes("office") ? "wfo" :
        status.includes("home") ? "wfh" :
        status.includes("leave") ? "leave" : "unknown"
      );

      statusEl.textContent = `${entry.username || "unknown"}: ${entry.status}`;
      dayDiv.appendChild(statusEl);
    });

    calendar.appendChild(dayDiv);
  });
}

document.addEventListener("DOMContentLoaded", loadAttendance);
