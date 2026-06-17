import fs from "fs";

const raw = JSON.parse(fs.readFileSync("data/raw.json", "utf-8"));

function assert(condition, message) {
  if (!condition) throw new Error("❌ Schema error: " + message);
}

// ROOT STRUCTURE
assert(Array.isArray(raw.players), "players must be array");
assert(Array.isArray(raw.matches), "matches must be array");

// MATCH VALIDATION
raw.matches.forEach((m, i) => {
  assert(m.id, `match[${i}] missing id`);
  assert(m.homeTeam, `match[${i}] missing homeTeam`);
  assert(m.awayTeam, `match[${i}] missing awayTeam`);
  assert(m.status, `match[${i}] missing status`);

  assert(
    ["SCHEDULED", "FINISHED", "IN_PLAY"].includes(m.status),
    `match[${i}] invalid status`
  );

  assert(
    m.predictions && typeof m.predictions === "object",
    `match[${i}] missing predictions object`
  );
});

console.log("✅ Schema validation passed");
