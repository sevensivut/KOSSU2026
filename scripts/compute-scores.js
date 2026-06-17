import fs from "fs";

/* =========================================================
 1. LOAD ALL STATIC & DYNAMIC DATA
========================================================= */
let raw, predictions, players;

try {
    raw = JSON.parse(fs.readFileSync("data/raw.json", "utf-8"));
    predictions = JSON.parse(fs.readFileSync("data/predictions.json", "utf-8"));
    players = JSON.parse(fs.readFileSync("data/players.json", "utf-8"));
} catch (e) {
    console.error("❌ Failed to load data files:", e.message);
    process.exit(1);
}

console.log(`👥 Loaded ${players.length} players from players.json`);
console.log(`🏁 Loaded ${raw.matches.length} matches from raw.json`);
console.log(`🔮 Loaded ${Object.keys(predictions).length} match predictions from predictions.json`);

const matches = raw.matches || [];

/* =========================================================
 2. DYNAMIC WEIGHT CALCULATION
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
        while (j < 3 && counts[j].count === counts[i].count) {
            j++;
        }
        
        let sum = 0;
        for (let k = i + 1; k <= j; k++) {
            sum += k;
        }
        const avgWeight = sum / (j - i);
        
        for (let k = i; k < j; k++) {
            weights[counts[k].outcome] = avgWeight;
        }
        
        i = j;
    }
    
    return weights;
}

/* =========================================================
 3. SCORING LOGIC
========================================================= */
function scoreMatchPlayer(prediction, weights) {
    if (!prediction) return 0;
    const pred = String(prediction).toUpperCase();
    return weights[pred] || 0;
}

/* =========================================================
 4. PROCESS MATCHES
========================================================= */
function processMatches() {
    const scores = {};
    for (const player of players) {
        scores[player] = 0;
    }

    const enrichedMatches = matches.map(match => {
        const matchPredictions = predictions[match.id] || {};
        const weights = calculateWeights(matchPredictions);
        const enrichedPreds = {};

        for (const player of players) {
            const prediction = matchPredictions[player];
            const mScore = scoreMatchPlayer(prediction, weights);

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

    return { scores, enrichedMatches };
}

/* =========================================================
 5. LEADERBOARD & OUTPUT
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
    matches: result.enrichedMatches
};

fs.writeFileSync("data/matches.json", JSON.stringify(output, null, 2));

console.log("✅ Scoring complete");
console.log(`🏁 Matches processed: ${matches.length}`);
console.log(`👥 Players scored: ${players.length}`);
