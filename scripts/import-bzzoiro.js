import fs from "fs";

const GROUP_STAGE = {
  league_id: 27
};

const API_TOKEN = process.env.BZZOIRO_TOKEN;

if (!API_TOKEN) {
  throw new Error("Missing BZZOIRO_TOKEN");
}

// --- SMART FETCH LOGIC ---
function isFetchNeeded(matches) {
  if (!matches || matches.length === 0) return true; // First run

  const now = new Date();

  for (const m of matches) {
    const matchTime = new Date(m.date);
    const diffMinutes = (matchTime - now) / 60000;

    // 1. Match starts in the next 45 minutes
    if (diffMinutes > 0 && diffMinutes <= 45) return true;

    // 2. Match started recently (within last 3.5 hours)
    // This covers the live game + immediate post-game score updates
    const hoursSinceStart = -diffMinutes / 60;
    if (hoursSinceStart >= 0 && hoursSinceStart <= 3.5) return true;
    
    // 3. Match is currently LIVE (safety net)
    const liveStatuses = ["in_play", "live", "halftime", "1st_half", "2nd_half", "extratime", "penalties"];
    if (liveStatuses.includes(String(m.status).toLowerCase())) return true;
  }

  return false;
}

// --- MAIN EXECUTION ---
let existingMatches = [];
if (fs.existsSync("data/raw.json")) {
  try {
    const data = JSON.parse(fs.readFileSync("data/raw.json", "utf-8"));
    existingMatches = data.matches || [];
  } catch (e) {
    console.warn("Could not parse existing raw.json, forcing fetch.");
  }
}

if (!isFetchNeeded(existingMatches)) {
  console.log("💤 No active or upcoming matches in the immediate window. Skipping API call to be courteous.");
  process.exit(0); // Exit gracefully, do not fail the build
}

console.log("⚽ Match window active. Fetching fresh data from Bzzoiro API...");

async function fetchBzzoiro() {
  // Use season_id=188 to get the whole World Cup.
  // Use limit=200 to ensure we get all 72+ matches.
  const url = `https://sports.bzzoiro.com/api/v2/events/?season_id=188&limit=200`;

  const res = await fetch(url, {
    headers: {
      Authorization: `Token ${API_TOKEN}`
    }
  });

  if (!res.ok) {
    throw new Error(`BSD API error: ${res.status}`);
  }

  return await res.json();
}

function normalize(api) {
  const matches = api.results || [];

  return {
    players: [],
    matches: matches.map(m => ({
      id: String(m.id),
      date: m.event_date,
      homeTeam: m.home_team,
      awayTeam: m.away_team,
      status: mapStatus(m.status),
      score: {
        home: m.home_score ?? null,
        away: m.away_score ?? null
      },
      result: deriveResult({
        home: m.home_score,
        away: m.away_score
      }),
      predictions: {}
    }))
  };
}

function mapStatus(s) {
  if (!s) return "SCHEDULED";
  const map = {
    notstarted: "SCHEDULED",
    scheduled: "SCHEDULED",
    finished: "FINISHED",
    in_play: "IN_PLAY",
    live: "IN_PLAY",
    halftime: "IN_PLAY",
    "1st_half": "IN_PLAY",
    "2nd_half": "IN_PLAY"
  };
  return map[String(s).toLowerCase()] || "SCHEDULED";
}

function deriveResult(score) {
  if (!score || score.home == null || score.away == null) return null;
  if (score.home > score.away) return "1";
  if (score.home < score.away) return "2";
  return "X";
}

const api = await fetchBzzoiro();
const raw = normalize(api);

fs.writeFileSync(
  "data/raw.json",
  JSON.stringify(raw, null, 2)
);

console.log(`✅ Bzzoiro API → raw.json updated (${raw.matches.length} matches fetched)`);
