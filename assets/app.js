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
