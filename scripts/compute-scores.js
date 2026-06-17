import fs from "fs";

/* =========================================================
   LOAD RAW DATA
========================================================= */

const input = JSON.parse(
  fs.readFileSync("data/raw.json", "utf-8")
);

const matches = input.matches || [];
const players = input.players || [];

/* =========================================================
   1X2 WEIGHT SYSTEM
========================================================= */

function calculateWeights(match) {
  const counts = { "1": 0, "X": 0, "2": 0 };

  const votes = match.predictions || {};

  for (const v of Object.values(votes)) {
    if (counts[v] !== undefined) counts[v]++;
  }

  const sorted = Object.entries(counts)
    .sort((a, b) => a[1] - b[1]); // least → most

  // fallback safety
  if (sorted.length < 3) {
    return { weights: { "1": 2, "X": 2, "2": 2 }, multiplier: 1 };
  }

  const weights = {
    [sorted[2][0]]: 1,
    [sorted[1][0]]: 2,
    [sorted[0][0]]: 3,
  };

  const values = Object.values(counts);
  const unique = new Set(values).size;

  let multiplier = 1;

  // tie logic from your rules
  if (unique === 2) multiplier = 1.5;
  if (unique === 1) multiplier = 2.5;

  return { weights, multiplier };
}

/* =========================================================
   PLAYER MATCH SCORE
========================================================= */

function scoreMatchPlayer(match, player, weights, multiplier) {
  const pred = match.predictions?.[player];
  if (!pred) return 0;

  return (weights[pred] || 0) * multiplier;
}

/* =========================================================
   PODIUM SCORING
========================================================= */

function scorePodium(match, player) {
  const p = match.podiumPrediction?.[player];
  const actual = match.podium;

  if (!p || !actual) return 0;

  let score = 0;

  for (const k of ["gold", "silver", "bronze"]) {
    if (p[k] === actual[k]) {
      score += 3;
    } else if (Object.values(actual).includes(p[k])) {
      score += 1;
    }
  }

  return score;
}

/* =========================================================
   PROCESS MATCHES
========================================================= */

function processMatches() {
  const scores = {};
  players.forEach(p => (scores[p] = 0));

  const enrichedMatches = matches.map(match => {
    const { weights, multiplier } = calculateWeights(match);

    const enrichedPreds = {};

    for (const player of players) {
      const mScore = scoreMatchPlayer(match, player, weights, multiplier);
      const pScore = scorePodium(match, player);

      scores[player] += mScore + pScore;

      enrichedPreds[player] = {
        prediction: match.predictions?.[player] || null,
        matchPoints: mScore,
        podiumPoints: pScore,
        total: mScore + pScore
      };
    }

    return {
      ...match,
      weights,
      multiplier,
      enrichedPredictions: enrichedPreds
    };
  });

  return { scores, enrichedMatches };
}

/* =========================================================
   LEADERBOARD
========================================================= */

function buildLeaderboard(scores) {
  return Object.entries(scores)
    .map(([name, points]) => ({ name, points }))
    .sort((a, b) => b.points - a.points);
}

/* =========================================================
   OUTPUT
========================================================= */

const { scores, enrichedMatches } = processMatches();
const leaderboard = buildLeaderboard(scores);

const output = {
  updatedAt: new Date().toISOString(),
  players,
  scores,
  leaderboard,
  matches: enrichedMatches
};

fs.writeFileSync(
  "data/matches.json",
  JSON.stringify(output, null, 2)
);

console.log("✅ Scoring complete");
console.log(`🏁 Matches: ${matches.length}`);
console.log(`👥 Players: ${players.length}`);
