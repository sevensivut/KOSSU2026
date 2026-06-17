import fs from "fs";

let raw, predictions, players;

try {
    raw = JSON.parse(fs.readFileSync("data/raw.json", "utf-8"));
    console.log("✅ raw.json is valid");
} catch (e) {
    console.error("❌ SYNTAX ERROR in data/raw.json:", e.message);
    process.exit(1);
}

try {
    predictions = JSON.parse(fs.readFileSync("data/predictions.json", "utf-8"));
    console.log("✅ predictions.json is valid");
} catch (e) {
    console.error("❌ SYNTAX ERROR in data/predictions.json:", e.message);
    process.exit(1);
}

try {
    players = JSON.parse(fs.readFileSync("data/players.json", "utf-8"));
    console.log("✅ players.json is valid");
} catch (e) {
    console.error("❌ SYNTAX ERROR in data/players.json:", e.message);
    process.exit(1);
}

console.log(`👥 Loaded ${players.length} players`);
console.log(`🏁 Loaded ${raw.matches.length} matches`);
console.log(`🔮 Loaded ${Object.keys(predictions).length} match predictions`);

const matches = raw.matches || [];
