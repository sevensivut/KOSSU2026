import fs from "fs";

/* =========================================================
 1. LOAD DATA
========================================================= */
let rawInput, predictionsInput;

try {
    rawInput = JSON.parse(fs.readFileSync("data/raw.json", "utf-8"));
} catch (e) {
    console.error("❌ Could not read data/raw.json. Did import-bzzoiro.js run?");
    process.exit(1);
}

try {
    predictionsInput = JSON.parse(fs.readFileSync("data/predictions.json", "utf-8"));
} catch (e) {
    console.error("❌ Could not read data/predictions.json.");
    process.exit(1);
}

const matches = rawInput.matches || [];

/* =========================================================
 2. EXTRACT PLAYERS FROM PREDICTIONS.JSON
========================================================= */
// Get the player names from the keys of the first match in predictions.json
const firstMatchId = Object.keys(predictionsInput)[0];
const players = firstMatchId ? Object.keys(predictionsInput[firstMatchId]) : [];

console.log(`👥 Found ${players.length} players in predictions.json: ${players.join(", ")}`);

/* =========================================================
 3. DYNAMIC WEIGHT CALCULATION
========================================================= */
function calculateWeights(predictions) {
    let c1 = 0, c2 = 0, cX = 0;
    
    for (const player in predictions) {
        const p = String(predictions[player]).toUpperCase();
        if (p === "1") c1++;
        else if (p === "2") c2++;
        else if (p === "X") cX++;
    }
    
    const counts = [
        { outcome: "1", count: c1 },
        { outcome: "2", count: c2 },
        { outcome: "X", count: cX }
    ];
    
    // Sort descending by popularity (highest count first)
    counts.sort((a, b) => b.count - a.count);
    
    const weights = { "1": 0, "2": 0, "X": 0 };
    
    // Assign points based on rank (1, 2, 3) with average for ties
    let i = 0;
    while (i < 3) {
        let j = i;
        // Find all outcomes with the exact same count (ties)
        while (j < 3 && counts[j].count === counts[i].count) {
            j++;
        }
        
        // Calculate the average of the positions they span
        let sum = 0;
        for (let k = i + 1; k <= j; k++) {
            sum += k;
        }
        const avgWeight = sum / (j - i);
        
        // Assign this weight to all tied outcomes
        for (let k = i; k < j; k++) {
            weights[counts[k].outcome] = avgWeight;
        }
        
        i = j;
    }
    
    return weights;
}

/* =========================================================
 4. SCORING LOGIC
========================================================= */
function scoreMatchPlayer(prediction, weights) {
    if (!prediction) return 0;
    const pred = String(prediction).toUpperCase();
    return weights[pred] || 0;
}

/* =========================================================
 5. PROCESS MATCHES
========================================================= */
function processMatches() {
    const scores = {};
    for (let i = 0; i < players.length; i++) {
        scores[players[i]] = 0;
    }

    const enrichedMatches = matches.map(match => {
        // 1. Get the predictions for this specific match from predictions.json
        const matchPredictions = predictionsInput[match.id] || {};
        
        // 2. Calculate weights dynamically for THIS specific match
        const weights = calculateWeights(matchPredictions);
        const enrichedPreds = {};

        // 3. Score each player
        for (let i = 0; i < players.length; i++) {
            const player = players[i];
            const prediction = matchPredictions[player];
            const mScore = scoreMatchPlayer(prediction, weights);

            scores[player] += mScore;

            enrichedPreds[player] = {
                prediction: prediction || null,
                matchPoints: mScore,
                total: mScore
            };
        }

        const newMatch = Object.assign({}, match);
        newMatch.predictions = matchPredictions; // Attach the actual predictions to the match
        newMatch.weights = weights; // Save weights for the frontend
        newMatch.enrichedPredictions = enrichedPreds;
        return newMatch;
    });

    return { scores: scores, enrichedMatches: enrichedMatches };
}

/* =========================================================
 6. LEADERBOARD
========================================================= */
function buildLeaderboard(scores
