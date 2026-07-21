const fs = require('fs');
let file = fs.readFileSync('frontend/src/routes/quiz/+page.svelte', 'utf8');

file = file.replace('function getLevel(total) {', '/** @param {number} total */\n    function getLevel(total) {');
file = file.replace('function getScore100(total) {', '/** @param {number} total */\n    function getScore100(total) {');
file = file.replace('function setVersion(v) {', '/** @param {string} v */\n    function setVersion(v) {');
file = file.replace('function selectOpt(pts) {', '/** @param {number} pts */\n    function selectOpt(pts) {');

file = file.replace('const BLOCK_MSG = {', '/** @type {Record<number, string>} */\n    const BLOCK_MSG = {');
file = file.replace('const answersRecord = {};', '/** @type {Record<string, any>} */\n                const answersRecord = {};');


fs.writeFileSync('frontend/src/routes/quiz/+page.svelte', file);
