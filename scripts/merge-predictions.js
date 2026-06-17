import fs from "fs";

// Load raw match data from Bzzoiro
const raw = JSON.parse(fs.readFileSync("data/raw.json", "utf-8"));

// Load player predictions
const predictions = JSON.parse(fs.readFileSync("data/predictions.json", "utf-8"));

// Extract players from predictions.json (use first match)
const firstMatchId = Object.keys(predictions)[0];
const players = firstMatchId ? Object.keys(predictions[firstMatchId]) : [];

// Inject predictions into each match
const enrichedMatches = raw.matches.map(match => {
  const preds = predictions[match.id] || {};
  return {
    ...match,
    predictions: preds
  };
});

// Write back to raw.json so it passes validation
const output = {
  players: players,
  matches: enrichedMatches
};

fs.writeFileSync("data/raw.json", JSON.stringify(output, null, 2));

console.log("✅ Merged predictions.json into raw.json");
console.log(`👥 Players: ${players.length}`);
console.log(`🏁 Matches enriched: ${enrichedMatches.length}`);
