let data = null;

const $ = id => document.getElementById(id);

async function loadData() {
  try {
    const response = await fetch(
      `data/matches.json?v=${Date.now()}`
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    data = await response.json();

    renderAll();

  } catch (err) {
    showError(err.message);
    console.error(err);
  }
}

function renderAll() {
  renderHeader();
  renderStats();
  renderLeaderboard();
  renderMatches();
  renderAwards();
}

function renderHeader() {
  const d = new Date(data.updatedAt);

  $("updatedAt").textContent =
    `Päivitetty ${d.toLocaleString("fi-FI")}`;
}

function renderStats() {

  const completed =
    data.matches.filter(
      m => m.status === "FINISHED"
    ).length;

  const leader =
    Object.entries(data.scores)
      .sort((a,b)=>b[1]-a[1])[0];

  $("stats").innerHTML = `
    <div class="card">
      <div class="card-value">${leader[0]}</div>
      <div class="card-label">Johtaja</div>
    </div>

    <div class="card">
      <div class="card-value">${leader[1]}</div>
      <div class="card-label">Pistettä</div>
    </div>

    <div class="card">
      <div class="card-value">${completed}/${data.matchCount}</div>
      <div class="card-label">Pelattu</div>
    </div>

    <div class="card">
      <div class="card-value">${data.liveCount}</div>
      <div class="card-label">Live</div>
    </div>
  `;
}

function renderLeaderboard() {

  const sorted =
    Object.entries(data.scores)
      .sort((a,b)=>b[1]-a[1]);

  $("leaderboard").innerHTML =
    sorted.map((p,index)=>{

      let medal = index+1;

      if(index===0) medal="🥇";
      if(index===1) medal="🥈";
      if(index===2) medal="🥉";

      return `
      <div class="leader-row">
        <div>
          <span class="rank">${medal}</span>
          ${p[0]}
        </div>

        <div class="points">
          ${p[1]}
        </div>
      </div>
      `;
    }).join("");
}

function renderMatches() {

  const search =
    $("teamSearch")?.value?.toLowerCase() || "";

  const matches =
    data.matches.filter(m => {

      if(!search) return true;

      return (
        m.homeTeam.toLowerCase().includes(search)
        ||
        m.awayTeam.toLowerCase().includes(search)
      );
    });

  $("matchesList").innerHTML =
    matches.map(m => {

      const popular =
        mostPopularPrediction(m);

      return `
      <details class="match">
        <summary>

          <strong>
            ${m.homeTeam}
            –
            ${m.awayTeam}
          </strong>

          <br>

          ${new Date(m.date)
            .toLocaleString("fi-FI")}

          <br>

          🔥 Kansan veikkaus:
          ${popular}
        </summary>

        <div class="predictions">

          ${
            Object.entries(m.predictions)
              .map(([name,pred]) => `
                <div class="pred">
                  <span>${name}</span>
                  <strong>${pred}</strong>
                </div>
              `)
              .join("")
          }

        </div>
      </details>
      `;
    }).join("");
}

function mostPopularPrediction(match){

  const counts = {
    "1":0,
    "X":0,
    "2":0
  };

  Object.values(match.predictions)
    .forEach(v => counts[v]++);

  return Object.entries(counts)
    .sort((a,b)=>b[1]-a[1])[0][0];
}

function renderAwards() {

  const sorted =
    Object.entries(data.scores)
      .sort((a,b)=>b[1]-a[1]);

  $("awardsGrid").innerHTML = `
    <div class="awards">

      <div class="card">
        <h3>🥇 Mestari</h3>
        <p>${sorted[0][0]}</p>
      </div>

      <div class="card">
        <h3>🥈 Hopea</h3>
        <p>${sorted[1][0]}</p>
      </div>

      <div class="card">
        <h3>🥉 Pronssi</h3>
        <p>${sorted[2][0]}</p>
      </div>

    </div>
  `;
}

function showError(msg){

  const box = $("errorBox");

  box.textContent = msg;
  box.classList.remove("hidden");
}

document
  .querySelectorAll(".tab")
  .forEach(btn => {

    btn.addEventListener("click",()=>{

      document
        .querySelectorAll(".tab")
        .forEach(t =>
          t.classList.remove("active"));

      btn.classList.add("active");

      const target =
        btn.dataset.tab;

      document
        .querySelectorAll(".tab-content")
        .forEach(c =>
          c.classList.add("hidden"));

      $(target)
        .classList
        .remove("hidden");
    });
  });

document.addEventListener(
  "input",
  e => {
    if(e.target.id==="teamSearch"){
      renderMatches();
    }
  }
);

loadData();
setInterval(loadData, 60000);
