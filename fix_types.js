const fs = require('fs');
let file = fs.readFileSync('frontend/src/routes/quiz/+page.svelte', 'utf8');

// Replace any[] with initialized typing
file = file.replace('let answers = [];', '/** @type {number[]} */\n    let answers = [];');
file = file.replace('let resultLevel = null;', '/** @type {any} */\n    let resultLevel = null;');
file = file.replace('let resultNextLevel = null;', '/** @type {any} */\n    let resultNextLevel = null;');
file = file.replace('let currentUser = null;', '/** @type {any} */\n    let currentUser = null;');
file = file.replace('let selected = null;', '/** @type {number | null} */\n    let selected = null;');

fs.writeFileSync('frontend/src/routes/quiz/+page.svelte', file);
