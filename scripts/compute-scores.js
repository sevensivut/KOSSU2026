import fs from "fs";

/* =========================================================
 1. LOAD DATA
========================================================= */
let input;
try {
    input = JSON.parse(fs.readFileSync("data/raw.json", "utf-8"));
} catch (e) {
    console.error("❌ Could not read data/raw.json. Did import-bzzoiro.js run successfully?");
    process.exit(1);
}

const matches = input.matches || [];

/* =========================================================
 2. EXTRACT PLAYERS FROM PREDICTIONS
========================================================= */
function extractPlayers(matches) {
    const playerSet = new Set();
    
    for (const match of matches) {
        if (match.predictions) {
            for (const player in match.predictions) {
                playerSet.add(player);
            }
        }
    }
    
    return Array.from(playerSet);
}

const players = extractPlayers(matches);

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
 4. SCORING LOGIC
========================================================= */
function scoreMatchPlayer(match, player, weights) {
    const pred = match.predictions ? String(match.predictions[player]).toUpperCase() : null;
    if (!pred) return 0;
    
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
            score += 3;
        } else if (Object.values(actual).includes(p[k])) {
            score += 1;
        }
    }
    return score;
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
        const weights = calculateWeights(match.predictions || {});
        const enrichedPreds = {};

        for (let i = 0; i < players.length; i++) {
            const player = players[i];
            const mScore = scoreMatchPlayer(match, player, weights);
            const pScore = scorePodium(match, player);

            scores[player] += mScore + pScore;

            enrichedPreds[player] = {
                prediction: match.predictions ? match.predictions[player] : null,
                matchPoints: mScore,
                podiumPoints: pScore,
                total: mScore + pScore
            };
        }

        const newMatch = Object.assign({}, match);
        newMatch.weights = weights;
        newMatch.enrichedPredictions = enrichedPreds;
        return newMatch;
    });

    return { scores: scores, enrichedMatches: enrichedMatches };
}

/* =========================================================
 6. LEADERBOARD
========================================================= */
function buildLeaderboard(scores) {
    const entries = Object.entries(scores);
    const mapped = entries.map(([name, points]) => ({ name: name, points: points }));
    
    mapped.sort((a, b) => b.points - a.points);
    return mapped;
}

/* =========================================================
 7. OUTPUT TO FILE
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
console.log(`🏁 Matches processed: ${matches.length}`);
console.log(`👥 Players scored: ${players.length}`);
