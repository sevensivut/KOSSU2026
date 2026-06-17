import fs from "fs";

/* =========================================================
 1. LOAD DATA
========================================================= */
const inputPath = "data/matches.json";
let input;
try {
    input = JSON.parse(fs.readFileSync(inputPath, "utf-8"));
} catch (e) {
    console.error("❌ Could not read data/matches.json. Did you run import-weights.js first?");
    process.exit(1);
}

const matches = input.matches || [];
const players = input.players || [];

/* =========================================================
 2. SCORING LOGIC
========================================================= */
function scoreMatchPlayer(match, player) {
    const pred = match.predictions ? match.predictions[player] : null;
    if (!pred) return 0;

    // Use the weights imported from the CSV
    const weights = match.weights || { "1": 0, "X": 0, "2": 0 };
    return weights[pred] || 0;
}

function scorePodium(match, player) {
    const p = match.podiumPrediction ? match.podiumPrediction[player] : null;
    const actual = match.podium;
    if (!p || !actual) return 0;

    let score = 0;
    const medals = ["gold", "silver", "bronze"];
    
    for (let i = 0; i < medals.length; i++) {
        const k = medals[i];
        if (p[k] === actual[k]) {
            score += 3; // Exact match
        } else if (Object.values(actual).includes(p[k])) {
            score += 1; // Correct team, wrong position
        }
    }
    return score;
}

/* =========================================================
 3. PROCESS MATCHES
========================================================= */
function processMatches() {
    const scores = {};
    for (let i = 0; i < players.length; i++) {
        scores[players[i]] = 0;
    }

    const enrichedMatches = matches.map(match => {
        const enrichedPreds = {};

        for (let i = 0; i < players.length; i++) {
            const player = players[i];
            const mScore = scoreMatchPlayer(match, player);
            const pScore = scorePodium(match, player);

            scores[player] += mScore + pScore;

            enrichedPreds[player] = {
                prediction: match.predictions ? match.predictions[player] : null,
                matchPoints: mScore,
                podiumPoints: pScore,
                total: mScore + pScore
            };
        }

        // Create a new object to avoid mutating the original match directly
        const newMatch = Object.assign({}, match);
        newMatch.enrichedPredictions = enrichedPreds;
        return newMatch;
    });

    return { scores: scores, enrichedMatches: enrichedMatches };
}

/* =========================================================
 4. LEADERBOARD
========================================================= */
function buildLeaderboard(scores) {
    const entries = Object.entries(scores);
    const mapped = entries.map(([name, points]) => ({ name: name, points: points }));
    
    // Sort descending by points
    mapped.sort((a, b) => b.points - a.points);
    return mapped;
}

/* =========================================================
 5. OUTPUT TO FILE
========================================================= */
const result = processMatches();
const leaderboard = buildLeaderboard(result.scores);

const output = {
    updatedAt: new Date().toISOString(),
    players: players,
    scores: result.scores,
    leaderboard: leaderboard,
    matches: result.enrichedMatches
};

fs.writeFileSync("data/matches.json", JSON.stringify(output, null, 2));

console.log("✅ Scoring complete");
console.log(`🏁 Matches: ${matches.length}`);
console.log(`👥 Players: ${players.length}`);
