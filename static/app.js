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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = {
    origin: originInput.dataset.code,
    destination: destinationInput.dataset.code,
    date: document.getElementById("date").value,
    include_hidden: document.getElementById("include-hidden").checked,
  };

  if (!body.origin || !body.destination) {
    showStatus("Pick both airports from the list.", true);
    return;
  }

  const button = form.querySelector(".go");
  button.disabled = true;
  results.hidden = true;
  showStatus(`<span class="spinner"></span>Searching ${body.origin} → ${body.destination} and the cities beyond it. New routes take a few seconds…`);

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) {
      showStatus(data.error || "Something went wrong.", true);
      return;
    }
    statusBox.hidden = true;
    lastResult = data;
    activeTab = "best";
    render();
  } catch (error) {
    showStatus("Couldn't reach the server. Is app.py running?", true);
  } finally {
    button.disabled = false;
  }
});

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
    `${names[r.origin]} (${r.origin}) → ${names[r.destination]} (${r.destination})`;

  const dateText = new Date(r.date + "T00:00").toLocaleDateString("en-IN", {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  });
  let meta = `${dateText} · ${r.cities_searched.length} routes checked ` +
    `(${r.cached_searches} saved, ${r.live_searches} live)`;
  if (r.problems.length) meta += ` · ${r.problems.length} couldn't be searched right now`;
  if (r.searches_left != null) meta += ` · ${r.searches_left} searches left this month`;
  document.getElementById("meta").textContent = meta;

  drawTabs();
  drawList();
  results.hidden = false;
}

function bestOverallTicket(r) {
  if (r.best_overall === "hidden") return r.best_hidden;
  if (r.best_overall === "normal") return r.best_normal;
  return null;
}

function drawTabs() {
  const r = lastResult;
  const best = bestOverallTicket(r);
  const tabs = [
    {
      id: "best",
      label: "Best overall",
      price: best ? rupees(best.price) : "–",
      sub: r.best_overall === "hidden" ? `Hidden city · save ${rupees(r.saving)}` : "Normal ticket",
    },
    {
      id: "normal",
      label: "Normal tickets",
      price: r.best_normal ? rupees(r.best_normal.price) : "–",
      sub: `${r.normal.length} options`,
    },
    {
      id: "hidden",
      label: "Hidden-city",
      price: r.best_hidden ? rupees(r.best_hidden.price) : "–",
      sub: `${r.hidden.length} options`,
    },
  ];

  sortTabs.innerHTML = "";
  for (const tab of tabs) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "sort-tab" + (tab.id === activeTab ? " active" : "");
    button.setAttribute("role", "tab");
    button.innerHTML =
      `<div class="label">${tab.label}</div>` +
      `<div class="price">${tab.price}</div>` +
      `<div class="sub">${escapeHtml(tab.sub)}</div>`;
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
    // Best overall: everything, cheapest first.
    tickets = [
      ...r.normal.map((t) => ({ ticket: t, hidden: false })),
      ...r.hidden.map((t) => ({ ticket: t, hidden: true })),
    ].sort((a, b) => a.ticket.price - b.ticket.price);
  }

  warning.hidden = !tickets.some((item) => item.hidden);
  list.innerHTML = "";

  if (tickets.length === 0) {
    const message = activeTab === "hidden"
      ? "No hidden-city tickets found for this trip. Normal tickets are your best bet."
      : "No flights found for this trip.";
    list.innerHTML = `<div class="empty">${message}</div>`;
    return;
  }

  tickets.slice(0, 30).forEach((item, index) => {
    list.appendChild(card(item.ticket, item.hidden, activeTab !== "normal" && activeTab !== "hidden" && index === 0));
  });
}

function card(t, hidden, isBest) {
  const r = lastResult;
  const el = document.createElement("article");
  el.className = "card" + (isBest ? " best" : "");

  // For a hidden-city ticket the traveller's trip ends at the first stop.
  const arrive = hidden ? t.first_stop_arrival_time : t.final_arrival_time;
  const arriveCode = hidden ? t.first_stop : t.final_destination;
  const duration = hidden ? t.first_leg_duration_min : t.duration_min;

  let stopsText;
  if (hidden) stopsText = `<span class="stops-text direct">You get off here</span>`;
  else if (t.stops === 0) stopsText = `<span class="stops-text direct">Direct</span>`;
  else stopsText = `<span class="stops-text via">${t.stops} stop${t.stops > 1 ? "s" : ""} · ${escapeHtml(t.first_stop)}</span>`;

  const badges = [];
  if (isBest) badges.push(`<span class="badge best">Best overall</span>`);
  if (hidden) badges.push(`<span class="badge hidden">Hidden city · get off at ${escapeHtml(t.first_stop)}</span>`);
  if (hidden && r.best_normal && t.price < r.best_normal.price) {
    badges.push(`<span class="badge saving">Save ${rupees(r.best_normal.price - t.price)}</span>`);
  }

  const note = hidden
    ? `<div class="note">Ticket is booked to <strong>${escapeHtml(r.airport_names[t.final_destination] || t.final_destination)} (${escapeHtml(t.final_destination)})</strong> via ${escapeHtml(t.flight_numbers)}. Leave the airport at ${escapeHtml(t.first_stop)} and skip the last flight.</div>`
    : `<div class="note">${escapeHtml(t.flight_numbers)}</div>`;

  const logo = t.airline_logo ? `<img src="${escapeHtml(t.airline_logo)}" alt="">` : "";
  const deal = t.search_url
    ? `<a class="deal" href="${escapeHtml(t.search_url)}" target="_blank" rel="noopener">View deal →</a>`
    : "";

  el.innerHTML = `
    <div class="card-main">
      ${badges.length ? `<div class="badges">${badges.join("")}</div>` : ""}
      <div class="flight">
        <div class="airline">${logo}<span>${escapeHtml(t.all_airlines)}</span></div>
        <div>
          <div class="time">${clock(t.departure_time)}</div>
          <div class="code">${escapeHtml(t.origin)}</div>
        </div>
        <div class="path">
          <div>${hoursMinutes(duration)}</div>
          <div class="line"></div>
          ${stopsText}
        </div>
        <div class="end">
          <div class="time">${clock(arrive)}</div>
          <div class="code">${escapeHtml(arriveCode)}</div>
        </div>
      </div>
      ${note}
    </div>
    <div class="card-side">
      <div class="big">${rupees(t.price)}</div>
      ${deal}
    </div>`;
  return el;
}
