import fs from "fs";

/* =========================================================
 1. LOAD ALL DATA
========================================================= */
let raw, predictions, players, podium;

try { 
    raw = JSON.parse(fs.readFileSync("data/raw.json", "utf-8")); 
    console.log("✅ raw.json is valid"); 
} catch (e) { 
    console.error("❌ SYNTAX ERROR in raw.json:", e.message); 
    process.exit(1); 
}

try { 
    predictions = JSON.parse(fs.readFileSync("data/predictions.json", "utf-8")); 
    console.log("✅ predictions.json is valid"); 
} catch (e) { 
    console.error("❌ SYNTAX ERROR in predictions.json:", e.message); 
    process.exit(1); 
}

try { 
    players = JSON.parse(fs.readFileSync("data/players.json", "utf-8")); 
    console.log("✅ players.json is valid"); 
} catch (e) { 
    console.error("❌ SYNTAX ERROR in players.json:", e.message); 
    process.exit(1); 
}

try { 
    podium = JSON.parse(fs.readFileSync("data/podium.json", "utf-8")); 
    console.log("✅ podium.json is valid"); 
} catch (e) { 
    console.error("❌ SYNTAX ERROR in podium.json:", e.message); 
    process.exit(1); 
}

console.log(`👥 Loaded ${players.length} players`);
console.log(`🏁 Loaded ${raw.matches.length} matches`);
console.log(`🔮 Loaded ${Object.keys(predictions).length} match predictions`);

const matches = raw.matches || [];

/* =========================================================
 2. TEAM-NAME LOOKUP
    predictions.json is keyed by "HomeTeam|AwayTeam" using
    Bzzoiro's exact English team names, so no ID or ordering
    assumptions are needed.
========================================================= */
const mappedPredictions = {};
let unmatched = 0;

for (const match of matches) {
    const key     = `${match.homeTeam}|${match.awayTeam}`;
    const altKey  = `${match.awayTeam}|${match.homeTeam}`;
    const preds   = predictions[key] ?? predictions[altKey] ?? null;

    if (preds) {
        mappedPredictions[match.id] = preds;
    } else if (match.homeTeam && match.awayTeam
               && !match.homeTeam.startsWith("W")
               && !match.homeTeam.startsWith("L")
               && !/^\d/.test(match.homeTeam)
               && !match.homeTeam.includes("/")) {
        // Only warn for real teams, not knockout placeholders
        console.warn(`⚠️  No predictions for: ${key}`);
        unmatched++;
    }
}

console.log(`🔗 Matched ${Object.keys(mappedPredictions).length} predictions by team name (${unmatched} unmatched)`);

/* =========================================================
 3. DYNAMIC WEIGHT CALCULATION
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
        while (j < 3 && counts[j].count === counts[i].count) j++;
        let sum = 0;
        for (let k = i + 1; k <= j; k++) sum += k;
        const avgWeight = sum / (j - i);
        for (let k = i; k < j; k++) weights[counts[k].outcome] = avgWeight;
        i = j;
    }
    return weights;
}

/* =========================================================
 4. SCORING LOGIC (WITH LIVE SUPPORT)
========================================================= */
function scoreMatchPlayer(prediction, weights, actualResult, matchStatus) {
    if (!prediction) return 0;
    
    const pred = String(prediction).toUpperCase();
    const status = String(matchStatus || "").toUpperCase();
    
    // Award points for FINISHED matches
    if (actualResult && pred === actualResult) {
        return weights[pred] || 0;
    }
    
    // Award PROVISIONAL points for LIVE matches based on current score
    if ((status === "IN_PLAY" || status === "LIVE") && actualResult && pred === actualResult) {
        return weights[pred] || 0;
    }
    
    return 0;
}

/* =========================================================
 5. PROCESS MATCHES
========================================================= */
function processMatches() {
    const scores = {};
    for (const player of players) scores[player] = 0;

    const enrichedMatches = matches.map(match => {
        const actualResult = match.result; 
        const matchPredictions = mappedPredictions[match.id] || {};
        const weights = calculateWeights(matchPredictions);
        const enrichedPreds = {};

        for (const player of players) {
            const prediction = matchPredictions[player];
            const mScore = scoreMatchPlayer(prediction, weights, actualResult, match.status);
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
 6. LEADERBOARD & OUTPUT
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
    matches: result.enrichedMatches,
    podiumPredictions: podium,
    podiumActual: null
};

fs.writeFileSync("data/matches.json", JSON.stringify(output, null, 2));

console.log("✅ Scoring complete");
console.log(`🏁 Matches processed: ${matches.length}`);
console.log(`👥 Players scored: ${players.length}`);
