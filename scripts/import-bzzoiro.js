import fs from "fs";

const GROUP_STAGE = {
  date_from: "2026-06-11",
  date_to: "2026-06-28",
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
      Authorization: `Bearer ${API_TOKEN}`
    }
  });

  if (!res.ok) {
    throw new Error(`BSD API error: ${res.status}`);
  }

  return await res.json();
}

function normalize(api) {
  return {
    players: [], // unchanged (your system source)
    matches: (api.events || []).map(m => ({
      id: String(m.id),

      date: m.kickoff_time || m.date,

      homeTeam: m.home?.name,
      awayTeam: m.away?.name,

      status: mapStatus(m.status),

      score: {
        home: m.score?.home ?? null,
        away: m.score?.away ?? null
      },

      result: deriveResult(m.score),

      predictions: {}
    }))
  };
}

function mapStatus(s) {
  if (!s) return "SCHEDULED";

  const map = {
    scheduled: "SCHEDULED",
    finished: "FINISHED",
    in_play: "IN_PLAY",
    live: "IN_PLAY"
  };

  return map[s.toLowerCase()] || "SCHEDULED";
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
