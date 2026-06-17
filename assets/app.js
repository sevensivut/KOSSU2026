let data = null;

const $ = (id) => document.getElementById(id);

/* =========================================================
   LOAD DATA
========================================================= */

async function loadData() {
  try {
    const response = await fetch(`data/matches.json?v=${Date.now()}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    data = await response.json();

    renderAll();

  } catch (err) {
    console.error(err);
    showError(err.message);
  }
}

/* =========================================================
   MASTER RENDER
========================================================= */

function renderAll() {
  if (!data) return;

  renderHeader();
  renderStats();
  renderLeaderboard();
  renderMatches();
  renderAwards();
}

/* =========================================================
   HEADER
========================================================= */

function renderHeader() {
  const el = $("updatedAt");

  if (!data?.updatedAt) {
    el.textContent = "Päivitetty —";
    return;
  }

  const d = new Date(data.updatedAt);

  el.textContent = !isNaN(d)
    ? `Päivitetty ${d.toLocaleString("fi-FI")}`
    : "Päivitetty —";
}

/* =========================================================
   STATS
========================================================= */

function renderStats() {
  const scores = data?.scores || {};
  const matches = data?.matches || [];

  const entries = Object.entries(scores);

  if (!entries.length) {
    $("stats").innerHTML = `<div class="card">Ei dataa</div>`;
    return;
  }

  const sorted = [...entries].sort((a, b) => b[1] - a[1]);
  const leader = sorted[0];

  const completed = matches.filter(m => m.status === "FINISHED").length;

  $("stats").innerHTML = `
    <div class="card">
      <div class="card-value">${leader?.[0] ?? "—"}</div>
      <div class="card-label">Johtaja</div>
    </div>

    <div class="card">
      <div class="card-value">${leader?.[1] ?? "—"}</div>
      <div class="card-label">Pisteet</div>
    </div>

    <div class="card">
      <div class="card-value">${completed}/${data.matchCount ?? matches.length}</div>
      <div class="card-label">Pelattu</div>
    </div>

    <div class="card">
      <div class="card-value">${data.liveCount ?? 0}</div>
      <div class="card-label">Live</div>
    </div>
  `;
}

/* =========================================================
   LEADERBOARD
========================================================= */

function renderLeaderboard() {
  const scores = data?.scores || {};
  const entries = Object.entries(scores);

  if (!entries.length) {
    $("leaderboard").innerHTML = `<div class="card">Ei pisteitä</div>`;
    return;
  }

  const sorted = [...entries].sort((a, b) => b[1] - a[1]);

  $("leaderboard").innerHTML = sorted.map((p, index) => {
    let medal = index + 1;

    if (index === 0) medal = "🥇";
    else if (index === 1) medal = "🥈";
    else if (index === 2) medal = "🥉";

    return `
      <div class="leader-row">
        <div>
          <span class="rank">${medal}</span>
          ${p?.[0] ?? "—"}
        </div>

        <div class="points">
          ${p?.[1] ?? 0}
        </div>
      </div>
    `;
  }).join("");
}

/* =========================================================
   MATCHES
========================================================= */

function renderMatches() {
  const container = $("matchesList");

  const matches = data?.matches || [];

  const search = $("teamSearch")?.value?.toLowerCase() || "";

  const filtered = matches.filter(m => {
    if (!search) return true;

    return (
      (m.homeTeam || "").toLowerCase().includes(search) ||
      (m.awayTeam || "").toLowerCase().includes(search)
    );
  });

  if (!filtered.length) {
    container.innerHTML = `<div class="card">Ei otteluita</div>`;
    return;
  }

  container.innerHTML = filtered.map(m => {

    const home = m.homeTeam ?? "—";
    const away = m.awayTeam ?? "—";

    const dateObj = m.date ? new Date(m.date) : null;

    const dateStr =
      dateObj && !isNaN(dateObj)
        ? dateObj.toLocaleString("fi-FI")
        : "—";

    const popular = mostPopularPrediction(m);

    const preds = Object.entries(m.predictions || {});

    return `
      <details class="match">
        <summary>
          <strong>${home} – ${away}</strong>
          <br>
          ${dateStr}
          <br>
          🔥 Kansan veikkaus: ${popular}
        </summary>

        <div class="predictions">
          ${
            preds.length
              ? preds.map(([name, pred]) => `
                  <div class="pred">
                    <span>${name}</span>
                    <strong>${pred}</strong>
                  </div>
                `).join("")
              : `<div class="pred">Ei veikkauksia</div>`
          }
        </div>
      </details>
    `;
  }).join("");
}

/* =========================================================
   MOST POPULAR PREDICTION
========================================================= */

function mostPopularPrediction(match) {
  const counts = { "1": 0, "X": 0, "2": 0 };

  Object.values(match?.predictions || {})
    .forEach(v => {
      if (counts[v] !== undefined) counts[v]++;
    });

  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

  return sorted.length ? sorted[0][0] : "—";
}

/* =========================================================
   AWARDS
========================================================= */

function renderAwards() {
  const scores = data?.scores || {};
  const entries = Object.entries(scores);

  if (entries.length < 1) {
    $("awardsGrid").innerHTML = `<div class="card">Ei dataa</div>`;
    return;
  }

  const sorted = [...entries].sort((a, b) => b[1] - a[1]);

  const g = sorted[0];
  const s = sorted[1];
  const b = sorted[2];

  $("awardsGrid").innerHTML = `
    <div class="card">
      <h3>🥇 Mestari</h3>
      <p>${g?.[0] ?? "—"}</p>
    </div>

    <div class="card">
      <h3>🥈 Hopea</h3>
      <p>${s?.[0] ?? "—"}</p>
    </div>

    <div class="card">
      <h3>🥉 Pronssi</h3>
      <p>${b?.[0] ?? "—"}</p>
    </div>
  `;
}

/* =========================================================
   ERROR HANDLING
========================================================= */

function showError(msg) {
  const box = $("errorBox");

  if (!box) return;

  box.textContent = msg;
  box.classList.remove("hidden");
}

/* =========================================================
   EVENTS
========================================================= */

document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t =>
      t.classList.remove("active")
    );

    btn.classList.add("active");

    const target = btn.dataset.tab;

    document.querySelectorAll(".tab-content").forEach(c =>
      c.classList.add("hidden")
    );

    $(target)?.classList.remove("hidden");
  });
});

document.addEventListener("input", (e) => {
  if (e.target.id === "teamSearch") {
    renderMatches();
  }
});

/* =========================================================
   INIT
========================================================= */

loadData();
setInterval(loadData, 60000);
