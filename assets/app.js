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
    if (!globalData) return;
    const totalMatches = globalData.matches.length;
    const finishedMatches = globalData.matches.filter(m => m.status === 'FINISHED').length;
    const totalPlayers = globalData.players.length;
    const topScore = globalData.leaderboard[0]?.points || 0;
    
    statsEl.innerHTML = `
      <div class="card">
        <div class="card-value">${totalPlayers}</div>
        <div class="card-label">Pelaajaa</div>
      </div>
      <div class="card">
        <div class="card-value">${finishedMatches} / ${totalMatches}</div>
        <div class="card-label">Ottelua pelattu</div>
      </div>
      <div class="card">
        <div class="card-value">${topScore.toFixed(1)}</div>
        <div class="card-label">Kärkipistettä</div>
      </div>
    `;
  }

  // 4. RENDER LEADERBOARD
  function renderLeaderboard() {
    if (!globalData.leaderboard) return;
    
    let html = '';
    
    globalData.leaderboard.forEach((p, i) => {
      const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '';
      html += `
        <div class="leader-row">
          <span class="rank">${i + 1}. ${medal} ${p.name}</span>
          <span class="points">${p.points.toFixed(1)} p</span>
        </div>
      `;
    });
    
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
      
      const scoreDisplay = isFinished && m.score && m.score.home !== null
        ? `<strong style="color:var(--gold2)">${m.score.home} - ${m.score.away}</strong>` 
        : `<span>${timeStr}</span>`;
        
      const weights = m.weights || { '1': 0, 'X': 0, '2': 0 };
      
      let predsHtml = '';
      globalData.players.forEach(player => {
        const pred = m.predictions?.[player] || '-';
        const pts = m.enrichedPredictions?.[player]?.matchPoints || 0;
        const isCorrect = isFinished && pred === m.result;
        
        const highlight = isCorrect ? 'color:var(--green); font-weight:bold;' : '';
        const ptsDisplay = pts > 0 ? `<span style="color:var(--gold); margin-left:8px;">+${pts}p</span>` : '';
        
        predsHtml += `
          <div class="pred">
            <span>${player}</span>
            <span style="${highlight}">${pred} ${isCorrect ? '✅' : ''} ${ptsDisplay}</span>
          </div>
        `;
      });

      html += `
        <details class="match">
          <summary>
            <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
              <strong>${m.homeTeam} - ${m.awayTeam}</strong>
              ${scoreDisplay}
            </div>
            <div style="color:var(--dim); font-size:0.85rem; margin-top:6px;">
              ${dateStr} &nbsp;|&nbsp; Painot: 1:${weights['1']}p &nbsp; X:${weights['X']}p &nbsp; 2:${weights['2']}p
            </div>
          </summary>
          <div class="predictions">
            ${predsHtml}
          </div>
        </details>
      `;
    });
    
    matchesListEl.innerHTML = visibleCount > 0 ? html : '<p style="color:var(--dim); text-align:center;">Ei otteluita hakusanalla.</p>';
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
    
    medals.forEach(medal => {
      html += `<div class="card" style="border-top: 3px solid ${medal.color};">`;
      html += `<h3 style="margin-top:0; color:${medal.color};">${medal.label}</h3>`;
      
      const picks = {};
      globalData.players.forEach(player => {
        const team = globalData.podiumPredictions[player][medal.key];
        if (!picks[team]) picks[team] = [];
        picks[team].push(player);
      });
      
      for (const [team, playersWhoPicked] of Object.entries(picks)) {
        html += `
          <div style="margin-bottom: 12px;">
            <div style="font-weight: 700; font-size: 1.1rem;">${team}</div>
            <div style="color: var(--dim); font-size: 0.9rem;">${playersWhoPicked.join(', ')}</div>
          </div>
        `;
      }
      html += `</div>`; // CLOSE CARD
    }); // CLOSE FOREACH

    awardsGridEl.className = 'awards'; // Apply CSS grid class
    awardsGridEl.innerHTML = html;
  } // CLOSE RENDER AWARDS

  // Initialize
  loadData();
});