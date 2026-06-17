import fs from "fs";

/**
 * STEP 1: Load Bzzoiro export (from your working system)
 */
const bzz = JSON.parse(
  fs.readFileSync("data/bzzoiro.json", "utf-8")
);

/**
 * STEP 2: Normalize Bzzoiro → KOSSU schema
 */
function normalize(bzz) {
  const matches = bzz.matches.map(m => ({
    id: String(m.id),

    date: m.kickoff || m.date,

    homeTeam: m.home.team,
    awayTeam: m.away.team,

    status: mapStatus(m.status),

    score: {
      home: m.score?.home ?? null,
      away: m.score?.away ?? null
    },

    // IMPORTANT: Bzzoiro provides result OR can be derived
    result: m.result || deriveResult(m.score),

    predictions: {} // still yours (NOT from Bzzoiro)
  }));

  return {
    players: bzz.players || [],
    matches
  };
}

/**
 * STEP 3: Status mapping (protects schema stability)
 */
function mapStatus(s) {
  if (!s) return "SCHEDULED";

  const map = {
    scheduled: "SCHEDULED",
    finished: "FINISHED",
    live: "IN_PLAY",
    in_play: "IN_PLAY"
  };

  return map[s.toLowerCase()] || "SCHEDULED";
}

/**
 * STEP 4: Safe result derivation
 */
function deriveResult(score) {
  if (!score) return null;

  if (score.home > score.away) return "1";
  if (score.home < score.away) return "2";
  return "X";
}

/**
 * STEP 5: Write raw.json
 */
const raw = normalize(bzz);

fs.writeFileSync(
  "data/raw.json",
  JSON.stringify(raw, null, 2)
);

console.log("✅ Bzzoiro → raw.json normalized");
