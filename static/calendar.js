// static/calendar.js

let attendanceData = {};
let allUsers = new Set();
let currentMonth = new Date();

async function loadAttendance() {
  try {
    const res = await fetch("/api/attendance");
    attendanceData = await res.json();
    allUsers.clear();

    Object.values(attendanceData).forEach(entries => {
      entries.forEach(e => allUsers.add(e.username || "unknown"));
    });

    populateUserDropdown();
    renderCalendar();
  } catch (error) {
    console.error("Failed to load attendance:", error);
  }
}

function populateUserDropdown() {
  const select = document.getElementById("userFilter");
  select.innerHTML = `<option value="">All Users</option>`;
  [...allUsers].sort().forEach(user => {
    const opt = document.createElement("option");
    opt.value = user;
    opt.textContent = user;
    select.appendChild(opt);
  });

  select.addEventListener("change", renderCalendar);
}

function renderCalendar() {
  const filterUser = document.getElementById("userFilter").value;
  const calendar = document.getElementById("calendar");
  const monthLabel = document.getElementById("monthLabel");

  calendar.innerHTML = "";

  const options = { month: "long", year: "numeric" };
  monthLabel.textContent = currentMonth.toLocaleDateString(undefined, options);

  const month = currentMonth.getMonth();
  const year = currentMonth.getFullYear();

  Object.keys(attendanceData)
    .sort()
    .reverse()
    .forEach(dateStr => {
      const date = new Date(dateStr);
      if (date.getMonth() !== month || date.getFullYear() !== year) return;

      const entries = attendanceData[dateStr].filter(e => !filterUser || e.username === filterUser);
      if (entries.length === 0) return;

      const dayDiv = document.createElement("div");
      dayDiv.className = "day";

      const displayDate = date.toLocaleDateString(undefined, {
        weekday: 'short', month: 'short', day: 'numeric'
      });

      const dateEl = document.createElement("div");
      dateEl.className = "date";
      dateEl.textContent = displayDate;
      dayDiv.appendChild(dateEl);

      if (dateStr === new Date().toISOString().split("T")[0]) {
        dayDiv.classList.add("today");
      }

      entries.forEach(entry => {
        const statusEl = document.createElement("div");
        const status = entry.status.toLowerCase();

        statusEl.className = "status " + (
          status.includes("office") ? "wfo" :
          status.includes("home") ? "wfh" :
          status.includes("leave") ? "leave" : "unknown"
        );

        statusEl.textContent = `${entry.username}: ${entry.status}`;
        dayDiv.appendChild(statusEl);
      });

      calendar.appendChild(dayDiv);
    });
}

// Navigation
document.getElementById("prevMonth").addEventListener("click", () => {
  currentMonth.setMonth(currentMonth.getMonth() - 1);
  renderCalendar();
});
document.getElementById("nextMonth").addEventListener("click", () => {
  currentMonth.setMonth(currentMonth.getMonth() + 1);
  renderCalendar();
});

document.addEventListener("DOMContentLoaded", loadAttendance);
