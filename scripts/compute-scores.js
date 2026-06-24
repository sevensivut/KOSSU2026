import fs from "fs";

/* =========================================================
 1. LOAD DATA
========================================================= */
let raw, predictionsByTeams, players, podium;

try { raw = JSON.parse(fs.readFileSync("data/raw.json", "utf-8")); } catch (e) { console.error("❌ raw.json:", e.message); process.exit(1); }
try { predictionsByTeams = JSON.parse(fs.readFileSync("data/predictions-by-teams.json", "utf-8")); } catch (e) { console.error("❌ predictions-by-teams.json:", e.message); process.exit(1); }
try { players = JSON.parse(fs.readFileSync("data/players.json", "utf-8")); } catch (e) { console.error("❌ players.json:", e.message); process.exit(1); }
try { podium = JSON.parse(fs.readFileSync("data/podium.json", "utf-8")); } catch (e) { console.error("❌ podium.json:", e.message); process.exit(1); }

console.log(`👥 ${players.length} players | 🏁 ${raw.matches.length} matches | 🔮 ${Object.keys(predictionsByTeams).length} prediction pairs`);

const matches = raw.matches || [];

/* =========================================================
 2. TEAM NAME NORMALIZATION (API → Finnish)
========================================================= */
const TEAM_ALIASES = {
  // English → Finnish
  "south korea": "Etelä-Korea",
  "korea republic": "Etelä-Korea",
  "usa": "USA",
  "united states": "USA",
  "united states of america": "USA",
  "côte d'ivoire": "Norsunluurannikko",
  "cote d'ivoire": "Norsunluurannikko",
  "ivory coast": "Norsunluurannikko",
  "cabo verde": "Kap Verde",
  "cape verde": "Kap Verde",
  "dr congo": "Kongon dem. tasavalta",
  "congo dr": "Kongon dem. tasavalta",
  "democratic republic of the congo": "Kongon dem. tasavalta",
  "bosnia & herzegovina": "Bosnia ja Hertsegovina",
  "bosnia-herzegovina": "Bosnia ja Hertsegovina",
  "bosnia and herzegovina": "Bosnia ja Hertsegovina",
  "türkiye": "Turkki",
  "turkey": "Turkki",
  "czechia": "Tšekki",
  "czech republic": "Tšekki",
  "curaçao": "Curaçao",
  "curacao": "Curaçao",
  "ir iran": "Iran",
};

function normalizeTeam(name) {
  if (!name) return "";
  const lower = name.trim().toLowerCase();
  return TEAM_ALIASES[lower] || name.trim();
}

function makeKey(home, away) {
  return `${normalizeTeam(home)}|${normalizeTeam(away)}`;
}

/* =========================================================
 3. DYNAMIC WEIGHT CALCULATION
========================================================= */
function calculateWeights(matchPredictions) {
  let c1 = 0, c2 = 0, cX = 0;
  for (const player of players) {
    const p = String(matchPredictions[player] || "").toUpperCase();
    if (p === "1") c1++;
    else if (p === "2") c2++;
    else if (p === "X") cX++;
  }

  const counts = [
    { outcome: "1", count: c1 },
    { outcome: "2", count: c2 },
    { outcome: "X", count: cX }
  ];
  counts.sort((a, b) => b.count - a.count);

  const weights = { "1": 0, "2": 0, "X": 0 };
  let i = 0;
  while (i < 3) {
    let j = i;
    while (j < 3 && counts[j].count === counts[i].count) j++;
    let sum = 0;
    for (let k = i + 1; k <= j; k++) sum += k;
    const avgWeight = sum / (j - i);
    for (let k = i; k < j; k++) weights[counts[k].outcome] = avgWeight;
    i = j;
  }
  return weights;
}

/* =========================================================
 4. SCORING LOGIC
========================================================= */
function scoreMatchPlayer(prediction, weights, actualResult, matchStatus) {
  if (!prediction) return 0;
  const pred = String(prediction).toUpperCase();
  const status = String(matchStatus || "").toUpperCase();

  if (actualResult && pred === actualResult) {
    return weights[pred] || 0;
  }
  if ((status === "IN_PLAY" || status === "LIVE") && actualResult && pred === actualResult) {
    return weights[pred] || 0;
  }
  return 0;
}

/* =========================================================
 5. PROCESS MATCHES (TEAM NAME MATCHING!)
========================================================= */
function processMatches() {
  const scores = {};
  for (const player of players) scores[player] = 0;

  let matchedCount = 0;
  let unmatched = [];

  const enrichedMatches = matches.map(match => {
    // Build key from API team names, normalized to Finnish
    const key = makeKey(match.homeTeam, match.awayTeam);
    const matchPredictions = predictionsByTeams[key] || {};

    if (Object.keys(matchPredictions).length > 0) {
      matchedCount++;
    } else {
      unmatched.push(`${match.homeTeam} vs ${match.awayTeam} (key: "${key}")`);
    }

    const weights = calculateWeights(matchPredictions);
    const enrichedPreds = {};

    for (const player of players) {
      const prediction = matchPredictions[player];
      const mScore = scoreMatchPlayer(prediction, weights, match.result, match.status);
      scores[player] += mScore;

      enrichedPreds[player] = {
        prediction: prediction || null,
        matchPoints: mScore,
        total: mScore
      };
    }

    return {
      ...match,
      predictions: matchPredictions,
      weights: weights,
      enrichedPredictions: enrichedPreds
    };
  });

  console.log(`✅ Matched ${matchedCount}/${matches.length} matches by team name`);
  if (unmatched.length > 0) {
    console.warn(`⚠️  ${unmatched.length} matches had no predictions:`);
    unmatched.forEach(u => console.warn(`   - ${u}`));
  }

  return { scores, enrichedMatches };
}

/* =========================================================
 6. LEADERBOARD & OUTPUT
========================================================= */
const result = processMatches();

const leaderboard = Object.entries(result.scores)
  .map(([name, points]) => ({ name, points }))
  .sort((a, b) => b.points - a.points);

const output = {
  updatedAt: new Date().toISOString(),
  players: players,
  scores: result.scores,
  leaderboard: leaderboard,
  matches: result.enrichedMatches,
  podiumPredictions: podium,
  podiumActual: null
};

fs.writeFileSync("data/matches.json", JSON.stringify(output, null, 2));

console.log("✅ Scoring complete");
console.log(`🏁 Matches processed: ${matches.length}`);
console.log(`👥 Players scored: ${players.length}`);
