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
  calendar.innerHTML = "";

  const options = { month: "long", year: "numeric" };
  document.getElementById("monthLabel").textContent = currentMonth.toLocaleDateString(undefined, options);

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDay = firstDay.getDay();
  const totalDays = lastDay.getDate();

  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  weekdays.forEach(day => {
    const header = document.createElement("div");
    header.className = "day-name";
    header.textContent = day;
    calendar.appendChild(header);
  });

  for (let i = 0; i < startDay; i++) {
    const empty = document.createElement("div");
    empty.className = "day empty";
    calendar.appendChild(empty);
  }

  const todayStr = new Date().toLocaleDateString('en-CA');

  for (let day = 1; day <= totalDays; day++) {
    const localDate = new Date(year, month, day);
    const dateStr = localDate.toLocaleDateString('en-CA');
    const entries = (attendanceData[dateStr] || []).filter(e => !filterUser || e.username === filterUser);

    const dayDiv = document.createElement("div");
    dayDiv.className = "day";
    if (dateStr === todayStr) {
      dayDiv.classList.add("today");
    }

    const dateEl = document.createElement("div");
    dateEl.className = "date";
    dateEl.textContent = day;
    dayDiv.appendChild(dateEl);

    entries.forEach(entry => {
      const statusEl = document.createElement("div");
      const status = entry.status.toLowerCase();
      statusEl.className = "status " + (
        status.includes("office") ? "wfo" :
        status.includes("home") ? "wfh" :
        status.includes("leave") ? "leave" : "unknown"
      );
      statusEl.textContent = `${entry.username}: ${entry.status}`;
      statusEl.title = `${entry.username}: ${entry.status}`;
      dayDiv.appendChild(statusEl);
    });

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
