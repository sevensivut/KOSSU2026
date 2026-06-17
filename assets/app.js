document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const tabs = document.querySelectorAll('.tab');
  const tabContents = document.querySelectorAll('.tab-content');
  const updatedAtEl = document.getElementById('updatedAt');
  const statsEl = document.getElementById('stats');
  const leaderboardEl = document.getElementById('leaderboard');
  const matchesListEl = document.getElementById('matchesList');
  const awardsGridEl = document.getElementById('awardsGrid');
  const teamSearchEl = document.getElementById('teamSearch');
  const errorBoxEl = document.getElementById('errorBox');

  let globalData = null;

  // 1. TAB NAVIGATION
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.classList.add('hidden'));
      
      tab.classList.add('active');
      const target = tab.getAttribute('data-tab');
      document.getElementById(target).classList.remove('hidden');
    });
  });

  // 2. FETCH DATA
  async function loadData() {
    try {
      // Cache-busting to ensure GitHub Pages loads the latest JSON
      const res = await fetch('data/matches.json?t=' + new Date().getTime()); 
      if (!res.ok) throw new Error('Dataa ei löytynyt');
      globalData = await res.json();
      
      renderAll();
    } catch (err) {
      showError('Virhe ladatessa dataa: ' + err.message);
    }
  }

  function showError(msg) {
    errorBoxEl.textContent = msg;
    errorBoxEl.classList.remove('hidden');
  }

  function renderAll() {
    renderUpdatedAt();
    renderStats();
    renderLeaderboard();
    renderMatches();
    renderAwards();
  }

  // 3. RENDER HEADER & STATS
  function renderUpdatedAt() {
    if (!globalData.updatedAt) return;
    const date = new Date(globalData.updatedAt);
    updatedAtEl.textContent = `Päivitetty: ${date.toLocaleDateString('fi-FI')} klo ${date.toLocaleTimeString('fi-FI', {hour: '2-digit', minute:'2-digit'})}`;
  }

  function renderStats() {
    const totalMatches = globalData.matches.length;
    const finishedMatches = globalData.matches.filter(m => m.status === 'FINISHED').length;
    const totalPlayers = globalData.players.length;
    const topScore = globalData.leaderboard[0]?.points || 0;
    
    statsEl.innerHTML = `
      <div class="stat-card">
        <h3>${totalPlayers}</h3>
        <p>Pelaajaa</p>
      </div>
      <div class="stat-card">
        <h3>${finishedMatches} / ${totalMatches}</h3>
        <p>Ottelua pelattu</p>
      </div>
      <div class="stat-card">
        <h3>${topScore.toFixed(1)}</h3>
        <p>Kärkipistettä</p>
      </div>
    `;
  }

  // 4. RENDER LEADERBOARD
  function renderLeaderboard() {
    if (!globalData.leaderboard) return;
    
    let html = `
      <table class="leaderboard-table">
        <thead>
          <tr>
            <th>Sija</th>
            <th>Pelaaja</th>
            <th>Pisteet</th>
          </tr>
        </thead>
        <tbody>
    `;
    
    globalData.leaderboard.forEach((p, i) => {
      const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '';
      html += `
        <tr>
          <td>${i + 1} ${medal}</td>
          <td>${p.name}</td>
          <td><strong>${p.points.toFixed(1)}</strong></td>
        </tr>
      `;
    });
    
    html += `</tbody></table>`;
    leaderboardEl.innerHTML = html;
  }

  // 5. RENDER MATCHES
  function renderMatches(filter = '') {
    if (!globalData.matches) return;
    
    // Sort chronologically
    const sortedMatches = [...globalData.matches].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    let html = '';
    let visibleCount = 0;
    
    sortedMatches.forEach(m => {
      const teams = `${m.homeTeam} ${m.awayTeam}`.toLowerCase();
      if (filter && !teams.includes(filter.toLowerCase())) return;
      visibleCount++;
      
      const date = new Date(m.date);
      const dateStr = date.toLocaleDateString('fi-FI', { weekday: 'short', day: '2-digit', month: '2-digit' });
      const timeStr = date.toLocaleTimeString('fi-FI', { hour: '2-digit', minute: '2-digit' });
      
      const isFinished = m.status === 'FINISHED';
      const statusClass = isFinished ? 'finished' : 'scheduled';
      
      const scoreDisplay = isFinished && m.score 
        ? `<span class="score">${m.score.home} - ${m.score.away}</span>` 
        : `<span class="time">${timeStr}</span>`;
        
      const weights = m.weights || { '1': 0, 'X': 0, '2': 0 };
        
      html += `
        <div class="match-card ${statusClass}">
          <div class="match-header">
            <span class="date">${dateStr}</span>
            ${scoreDisplay}
          </div>
          <div class="match-teams">
            <div class="team home">${m.homeTeam}</div>
            <div class="team away">${m.awayTeam}</div>
          </div>
          <div class="match-predictions">
            <h4>Veikkaukset <span class="weights">(1: ${weights['1']}p | X: ${weights['X']}p | 2: ${weights['2']}p)</span></h4>
            <div class="pred-grid">
      `;
      
      globalData.players.forEach(player => {
        const pred = m.predictions?.[player] || '-';
        const pts = m.enrichedPredictions?.[player]?.matchPoints || 0;
        const isCorrect = isFinished && pred === m.result;
        
        html += `
          <div class="pred-item ${isCorrect ? 'correct' : ''}">
            <span class="pred-player">${player}</span>
            <span class="pred-pick">${pred}</span>
            <span class="pred-pts">${pts > 0 ? '+' + pts : ''}</span>
          </div>
        `;
      });
      
      html += `
            </div>
          </div>
        </div>
      `;
    });
    
    matchesListEl.innerHTML = html || '<p>Ei otteluita hakusanalla.</p>';
  }

  teamSearchEl.addEventListener('input', (e) => {
    renderMatches(e.target.value);
  });
  
  // 6. RENDER AWARDS (PODIUM)
  function renderAwards() {
    if (!globalData.podiumPredictions) {
      awardsGridEl.innerHTML = '<p style="color:var(--dim); text-align:center;">Ei palkintopalliveikkauksia.</p>';
      return;
    }

    const medals = [
      { key: 'gold', label: '🥇 Kulta', color: 'var(--gold2)' },
      { key: 'silver', label: '🥈 Hopea', color: '#C0C0C0' },
      { key: 'bronze', label: '🥉 Pronssi', color: '#CD7F32' }
    ];

    let html = '';
    
    // Create a card for each medal category
    medals.forEach(medal => {
      html += `<div class="card" style="border-top: 3px solid ${medal.color};">`;
      html += `<h3 style="margin-top:0; color:${medal.color};">${medal.label}</h3>`;
      
      // Group players by their pick for this medal
      const picks = {};
      globalData.players.forEach(player => {
        const team = globalData.podiumPredictions[player][medal.key];
        if (!picks[team]) picks[team] = [];
        picks[team].push(player);
      });
      
      // Render the teams and who picked them
      for (const [team, playersWhoPicked] of Object.entries(picks)) {
        html += `
          <div style="margin-bottom: 12px;">
            <div style="font-weight: 700; font-size: 1.1rem;">${team}</div>
            <div style="color: var(--dim); font-size: 0.9rem;">${playersWhoPicked.join(', ')}</div>
          </div>
        `;
  // Initialize
  loadData();
});
