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

function getInitials(name) {
  return name
    .split(/[ ._]/)
    .filter(Boolean)
    .map(part => part[0].toUpperCase())
    .slice(0, 2)
    .join('');
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
  const todayStr = new Date().toISOString().split("T")[0];

  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  weekdays.forEach(day => {
    const header = document.createElement("div");
    header.className = "day header";
    header.textContent = day;
    calendar.appendChild(header);
  });

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  for (let i = 0; i < firstDay; i++) {
    const empty = document.createElement("div");
    empty.className = "day empty";
    calendar.appendChild(empty);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    const dateStr = date.toISOString().split("T")[0];
    const entries = (attendanceData[dateStr] || []).filter(
      e => !filterUser || e.username === filterUser
    );

    const dayDiv = document.createElement("div");
    dayDiv.className = "day date-cell";

    const dateEl = document.createElement("div");
    dateEl.className = "date";
    dateEl.textContent = day;
    dayDiv.appendChild(dateEl);

    if (dateStr === todayStr) {
      dayDiv.classList.add("today");
    }

    const grid = document.createElement("div");
    grid.className = "entry-grid";

    entries.forEach(entry => {
      const fullName = entry.username || "Unknown";
      const initials = getInitials(fullName);
      const status = entry.status.toLowerCase();

      const badge = document.createElement("div");
      badge.className = "initial-box " + (
        status.includes("office") ? "wfo" :
        status.includes("home") ? "wfh" :
        status.includes("leave") ? "leave" : "unknown"
      );

      badge.textContent = initials;
      badge.title = `${fullName} is on ${status}`;
      grid.appendChild(badge);
    });

    dayDiv.appendChild(grid);
    calendar.appendChild(dayDiv);
  }
}

document.getElementById("prevMonth").addEventListener("click", () => {
  currentMonth.setMonth(currentMonth.getMonth() - 1);
  renderCalendar();
});

document.getElementById("nextMonth").addEventListener("click", () => {
  currentMonth.setMonth(currentMonth.getMonth() + 1);
  renderCalendar();
});

document.addEventListener("DOMContentLoaded", loadAttendance);