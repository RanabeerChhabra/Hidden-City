// Runs the search form: sends it to /api/search and draws the results.

const form = document.getElementById("search");
const statusBox = document.getElementById("status");
const results = document.getElementById("results");
const list = document.getElementById("list");
const sortTabs = document.getElementById("sort-tabs");
const warning = document.getElementById("warning");

let lastResult = null;
let activeTab = "best";

// ---------- Airport boxes: type a city or code, pick from the list ----------

function label(airport) {
  return `${airport.city} (${airport.code})`;
}

function matches(query) {
  const q = query.trim().toLowerCase();
  if (!q) return window.AIRPORTS.slice(0, 8);
  const starts = [];
  const contains = [];
  for (const a of window.AIRPORTS) {
    const city = a.city.toLowerCase();
    const code = a.code.toLowerCase();
    if (code === q || city.startsWith(q)) starts.push(a);
    else if (code.startsWith(q) || city.includes(q)) contains.push(a);
  }
  return [...starts, ...contains].slice(0, 8);
}

function setupAirportBox(input) {
  const list = document.getElementById(input.getAttribute("aria-controls"));
  let options = [];
  let highlighted = 0;

  function choose(airport) {
    input.value = label(airport);
    input.dataset.code = airport.code;
    close();
  }

  function close() {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
  }

  function draw() {
    list.innerHTML = "";
    options.forEach((airport, i) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", i === highlighted ? "true" : "false");
      li.innerHTML = `<span>${escapeHtml(airport.city)}</span><span class="code">${airport.code}</span>`;
      // mousedown, not click: it fires before the input loses focus.
      li.addEventListener("mousedown", (event) => {
        event.preventDefault();
        choose(airport);
      });
      list.appendChild(li);
    });
    list.hidden = options.length === 0;
    input.setAttribute("aria-expanded", String(!list.hidden));
  }

  function open(query) {
    options = matches(query);
    highlighted = 0;
    draw();
  }

  input.addEventListener("focus", () => {
    input.select();
    open("");
  });
  input.addEventListener("input", () => {
    input.dataset.code = "";
    open(input.value);
  });
  input.addEventListener("keydown", (event) => {
    if (list.hidden) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      highlighted = (highlighted + step + options.length) % options.length;
      draw();
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (options[highlighted]) choose(options[highlighted]);
    } else if (event.key === "Escape") {
      close();
    }
  });
  input.addEventListener("blur", () => {
    // Typed something but didn't pick? Use the best match, if there is one.
    if (!input.dataset.code) {
      const best = matches(input.value)[0];
      if (best && input.value.trim()) choose(best);
    }
    close();
  });
}

const originInput = document.getElementById("origin");
const destinationInput = document.getElementById("destination");
setupAirportBox(originInput);
setupAirportBox(destinationInput);

document.getElementById("swap").addEventListener("click", () => {
  [originInput.value, destinationInput.value] = [destinationInput.value, originInput.value];
  [originInput.dataset.code, destinationInput.dataset.code] =
    [destinationInput.dataset.code, originInput.dataset.code];
});

let lastQuery = null;

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = {
    origin: originInput.dataset.code,
    destination: destinationInput.dataset.code,
    date: document.getElementById("date").value,
  };
  if (!query.origin || !query.destination) {
    showStatus("Pick both airports from the list.", true);
    return;
  }
  // Step 1: normal fares only (1 search). Hidden-city fares come on request.
  runSearch(query, false);
});

document.getElementById("hidden-go").addEventListener("click", () => {
  // Step 2: same trip, now also searching the cities beyond the destination.
  if (lastQuery) runSearch(lastQuery, true);
});

async function runSearch(query, includeHidden) {
  const button = form.querySelector(".go");
  button.disabled = true;
  results.hidden = true;
  showStatus(includeHidden
    ? `Searching cities past ${query.destination}. This takes a few seconds.`
    : `Searching ${query.origin} to ${query.destination}.`);

  try {
    const response = await fetch(window.SEARCH_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...query, include_hidden: includeHidden }),
    });
    const data = await response.json();
    if (!response.ok) {
      showStatus(data.error || "Something went wrong.", true);
      return;
    }
    statusBox.hidden = true;
    lastQuery = query;
    lastResult = data;
    activeTab = includeHidden ? "best" : "normal";
    render();
  } catch (error) {
    showStatus("Couldn't reach the server. Please try again.", true);
  } finally {
    button.disabled = false;
  }
}

function showStatus(html, isError = false) {
  statusBox.innerHTML = html;
  statusBox.classList.toggle("error", isError);
  statusBox.hidden = false;
}

function rupees(amount) {
  return "₹" + Number(amount).toLocaleString("en-IN");
}

function clock(timestamp) {
  // "2026-11-18 09:30" -> "09:30"
  return timestamp ? timestamp.split(" ")[1] : "";
}

function hoursMinutes(minutes) {
  if (!minutes) return "";
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, "0")}m`;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

function render() {
  const r = lastResult;
  const names = r.airport_names;
  document.getElementById("route-title").textContent =
    `${names[r.origin]} to ${names[r.destination]}`;

  const dateText = new Date(r.date + "T00:00").toLocaleDateString("en-IN", {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  });
  let meta = dateText;
  if (r.prices_age_minutes != null) {
    const m = r.prices_age_minutes;
    meta += m < 2 ? ". Prices checked just now."
      : m < 60 ? `. Prices checked ${m} min ago.`
      : `. Prices checked ${Math.round(m / 60)} h ago.`;
  }
  if (r.problems.length) {
    const n = r.problems.length;
    meta += ` ${n} ${n === 1 ? "search" : "searches"} failed, so this list may be missing fares.`;
  }
  document.getElementById("meta").textContent = meta;

  // Offer the longer-ticket check until it has been run for this trip.
  document.getElementById("hidden-cta").hidden = r.hidden_checked;
  if (!r.hidden_checked) {
    document.getElementById("hidden-cta-text").textContent =
      `Looks for tickets past ${names[r.destination]} that stop there first` +
      (r.hidden_cost ? `. Uses ${r.hidden_cost} more ${r.hidden_cost === 1 ? "search" : "searches"}.` : ".");
  }

  drawTabs();
  drawList();
  results.hidden = false;
}

function drawTabs() {
  const r = lastResult;
  const tabs = [
    { id: "normal", label: `Normal tickets (${r.normal.length})` },
  ];
  if (r.hidden_checked) {
    tabs.unshift({ id: "best", label: "All, cheapest first" });
    tabs.push({ id: "hidden", label: `Longer tickets (${r.hidden.length})` });
  }

  sortTabs.innerHTML = "";
  sortTabs.hidden = tabs.length === 1;
  for (const tab of tabs) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "tab" + (tab.id === activeTab ? " active" : "");
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", tab.id === activeTab ? "true" : "false");
    button.textContent = tab.label;
    button.addEventListener("click", () => {
      activeTab = tab.id;
      drawTabs();
      drawList();
    });
    sortTabs.appendChild(button);
  }
}

function drawList() {
  const r = lastResult;
  let tickets;
  if (activeTab === "normal") {
    tickets = r.normal.map((t) => ({ ticket: t, hidden: false }));
  } else if (activeTab === "hidden") {
    tickets = r.hidden.map((t) => ({ ticket: t, hidden: true }));
  } else {
    tickets = [
      ...r.normal.map((t) => ({ ticket: t, hidden: false })),
      ...r.hidden.map((t) => ({ ticket: t, hidden: true })),
    ].sort((a, b) => a.ticket.price - b.ticket.price);
  }

  warning.hidden = !tickets.some((item) => item.hidden);
  list.innerHTML = "";

  if (tickets.length === 0) {
    const message = activeTab === "hidden"
      ? "No longer tickets stop here on this date."
      : "No flights found for this date.";
    list.innerHTML = `<p class="empty">${message}</p>`;
    return;
  }

  const shown = tickets.slice(0, 30);
  shown.forEach((item, index) => list.appendChild(row(item.ticket, item.hidden, index === 0)));
  if (tickets.length > shown.length) {
    const more = document.createElement("p");
    more.className = "small more";
    more.textContent = `Showing the cheapest ${shown.length} of ${tickets.length}.`;
    list.appendChild(more);
  }
}

function row(t, hidden, isFirst) {
  const r = lastResult;
  const el = document.createElement("article");
  el.className = "row" + (isFirst ? " first" : "") + (hidden ? " longer" : "");

  // For a longer ticket, the traveller's trip ends at the first stop.
  const arrive = hidden ? t.first_stop_arrival_time : t.final_arrival_time;
  const duration = hidden ? t.first_leg_duration_min : t.duration_min;

  let length;
  if (hidden) length = `${hoursMinutes(duration)} to ${escapeHtml(t.first_stop)}`;
  else if (t.stops === 0) length = `${hoursMinutes(duration)}, direct`;
  else length = `${hoursMinutes(duration)}, via ${escapeHtml(t.first_stop)}`;

  let note = "";
  if (hidden) {
    const final = r.airport_names[t.final_destination] || t.final_destination;
    note = `Book to ${escapeHtml(final)} and get off at ${escapeHtml(r.airport_names[t.first_stop] || t.first_stop)}.`;
    if (r.best_normal) {
      const difference = r.best_normal.price - t.price;
      if (difference > 0) note += ` ${rupees(difference)} less than the cheapest normal ticket.`;
      else if (difference < 0) note += ` ${rupees(-difference)} more than the cheapest normal ticket.`;
    }
  }

  const logo = t.airline_logo ? `<img src="${escapeHtml(t.airline_logo)}" alt="">` : "";
  const deal = t.search_url
    ? `<a class="deal" href="${escapeHtml(t.search_url)}" target="_blank" rel="noopener">Google Flights</a>`
    : `<span></span>`;

  el.innerHTML = `
    <div class="times">${clock(t.departure_time)} to ${clock(arrive)}</div>
    <div class="who">${logo}<span>${escapeHtml(t.all_airlines)}</span> <span class="flight-no">${escapeHtml(t.flight_numbers)}</span></div>
    <div class="length">${length}</div>
    <div class="price">${rupees(t.price)}</div>
    ${deal}
    ${note ? `<div class="note">${note}</div>` : ""}`;
  return el;
}
