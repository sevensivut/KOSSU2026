import fs from "fs";

// 1. Load raw match data (from Bzzoiro API)
const rawPath = "data/raw.json";
const rawData = JSON.parse(fs.readFileSync(rawPath, "utf-8"));
const rawMatches = rawData.matches || [];

// 2. Load the CSV data
// Note: Ensure your CSV file is saved as data/kossu2026.csv
const csvPath = "data/kossu2026.csv";
const csvContent = fs.readFileSync(csvPath, "utf-8");
const lines = csvContent.trim().split("\n");

// Create a map of match ID to raw match object
const matchMap = {};
for (const m of rawMatches) {
    // Initialize with empty predictions and default 0 weights
    matchMap[m.id] = { ...m, predictions: {}, weights: { "1": 0, "X": 0, "2": 0 } };
}

// 3. Parse CSV rows and extract weights
// Skip the header row (i = 1)
for (let i = 1; i < lines.length; i++) {
    const parts = lines[i].split(",");
    if (parts.length < 58) continue; // Safety check for column count

    // Map CSV row to the Match ID (8308 to 8379)
    const matchId = String(8308 + (i - 1));
    
    // Extract weights from the specific CSV columns (indices 55, 56, 57)
    // These correspond to "painoarvo 1:lle", "painoarvo 2:lle", "painoarvo x:lle"
    const w1 = parseFloat(parts[55]);
    const w2 = parseFloat(parts[56]);
    const wx = parseFloat(parts[57]);

    const weights = {
        "1": isNaN(w1) ? 0 : w1,
        "2": isNaN(w2) ? 0 : w2,
        "X": isNaN(wx) ? 0 : wx
    };

    if (matchMap[matchId]) {
        // Update existing match with the imported weights
        matchMap[matchId].weights = weights;
    } else {
        // If the match isn't in the API data yet, create it from the CSV
        const dateStr = parts[0]; // e.g., "11.06.2026 22:00"
        const homeTeam = parts[1];
        const awayTeam = parts[3];
        
        // Convert date to ISO format (assuming Finnish time UTC+3 for the CSV)
        const [datePart, timePart] = dateStr.split(" ");
        const [d, m, y] = datePart.split(".");
        const isoDate = `${y}-${m}-${d}T${timePart}:00+03:00`;

        matchMap[matchId] = {
            id: matchId,
            date: isoDate,
            homeTeam: homeTeam,
            awayTeam: awayTeam,
            status: "SCHEDULED",
            score: { home: null, away: null },
            result: null,
            predictions: {},
            weights: weights,
            enrichedPredictions: {}
        };
    }
}

// Convert map back to array and sort by date
const matches = Object.values(matchMap);
matches.sort((a, b) => new Date(a.date) - new Date(b.date));

// 4. Save to matches.json
const output = {
    updatedAt: new Date().toISOString(),
    players: rawData.players || [],
    matches: matches
};

fs.writeFileSync("data/matches.json", JSON.stringify(output, null, 2));
console.log("✅ Weights imported and matches.json updated");
