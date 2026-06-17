import fs from "fs";

const GROUP_STAGE = {
  date_from: "2026-06-01",
  date_to: "2026-06-27",
  league_id: 27
};

const API_TOKEN = process.env.BZZOIRO_TOKEN;

if (!API_TOKEN) {
  throw new Error("Missing BZZOIRO_TOKEN");
}

async function fetchBzzoiro() {
  const url =
    `https://sports.bzzoiro.com/api/v2/events/` +
    `?date_from=${GROUP_STAGE.date_from}` +
    `&date_to=${GROUP_STAGE.date_to}` +
    `&league_id=${GROUP_STAGE.league_id}`;

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

function extractMatches(api) {
  return api.results || [];
}

function normalize(api) {
  const matches = extractMatches(api);

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
    live: "IN_PLAY"
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

console.log("✅ Bzzoiro API → raw.json updated");
