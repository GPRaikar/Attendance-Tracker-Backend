let attendanceData = {};
let allUsers = new Set();
let currentMonth = new Date();

// Utility to get initials
function getInitials(name) {
  if (!name) return "??";
  return name.split(" ")
             .map(w => w[0]?.toUpperCase())
             .join("")
             .slice(0, 3);
}

// Load attendance from backend
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

// Dropdown population
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

// Render calendar
function renderCalendar() {
  const filterUser = document.getElementById("userFilter").value;
  const calendar = document.getElementById("calendar");
  calendar.innerHTML = "";

  const options = { month: "long", year: "numeric" };
  document.getElementById("monthLabel").textContent = currentMonth.toLocaleDateString(undefined, options);

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDay = firstDay.getDay();
  const totalDays = lastDay.getDate();

  // Weekday headers (Sun to Sat)
  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  weekdays.forEach(day => {
    const header = document.createElement("div");
    header.className = "day-name";
    header.textContent = day;
    calendar.appendChild(header);
  });

  // Empty boxes before 1st
  for (let i = 0; i < startDay; i++) {
    const empty = document.createElement("div");
    empty.className = "day empty";
    calendar.appendChild(empty);
  }

  // Day boxes
  for (let day = 1; day <= totalDays; day++) {
    const dateObj = new Date(year, month, day);
    const dateStr = dateObj.toISOString().split("T")[0];

    const entries = (attendanceData[dateStr] || []).filter(e => !filterUser || e.username === filterUser);

    const dayDiv = document.createElement("div");
    dayDiv.className = "day";
    if (dateStr === new Date().toISOString().split("T")[0]) {
      dayDiv.classList.add("today");
    }

    const dateEl = document.createElement("div");
    dateEl.className = "date";
    dateEl.textContent = day;
    dayDiv.appendChild(dateEl);

    entries.forEach(entry => {
      const status = entry.status.toLowerCase();
      const shortStatus = status.includes("office") ? "WFO" :
                          status.includes("home") ? "WFH" :
                          status.includes("leave") ? "LV" : "??";

      const initials = getInitials(entry.username);

      const statusEl = document.createElement("div");
      statusEl.className = "status-tag " + (
        status.includes("office") ? "wfo" :
        status.includes("home") ? "wfh" :
        status.includes("leave") ? "leave" : "unknown"
      );
      statusEl.textContent = `${initials} (${shortStatus})`;

      dayDiv.appendChild(statusEl);
    });

    calendar.appendChild(dayDiv);
  }
}

// Navigation buttons
document.getElementById("prevMonth").addEventListener("click", () => {
  currentMonth.setMonth(currentMonth.getMonth() - 1);
  renderCalendar();
});

document.getElementById("nextMonth").addEventListener("click", () => {
  currentMonth.setMonth(currentMonth.getMonth() + 1);
  renderCalendar();
});

// Load data on DOM ready
document.addEventListener("DOMContentLoaded", loadAttendance);
