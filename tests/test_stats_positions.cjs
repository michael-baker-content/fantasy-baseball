const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../docs/stats-positions.js'), 'utf8');
const eligible = vm.runInNewContext(source + '\neligibleForStatsView;');
const player = (position, saves = 0) => ({position, stats: {SV: saves}});

test('infield includes catchers; outfield includes all outfield positions', () => {
  for (const position of ['C', '1B', '2B', '3B', 'SS']) {
    assert.equal(eligible(player(position), 'if'), true);
    assert.equal(eligible(player(position), 'of'), false);
  }
  for (const position of ['LF', 'CF', 'RF', 'OF']) {
    assert.equal(eligible(player(position), 'of'), true);
    assert.equal(eligible(player(position), 'if'), false);
  }
});
test('primary DH and missing positions remain in complete lists only', () => {
  for (const position of ['DH', '', undefined]) {
    assert.equal(eligible(player(position), 'batters'), true);
    for (const view of ['if', 'of', 'sp', 'rp']) assert.equal(eligible(player(position), view), false);
  }
  assert.equal(eligible(player(''), 'pitchers'), true);
});
test('generic P appears in both pitching subsets; RP remains RP', () => {
  assert.equal(eligible(player('P'), 'sp'), true);
  assert.equal(eligible(player('P'), 'rp'), true);
  assert.equal(eligible(player('RP'), 'rp'), true);
  assert.equal(eligible(player('RP'), 'sp'), false);
});
test('SP needs at least two saves to also appear in RP', () => {
  for (const saves of [0, 1, '1', '']) {
    assert.equal(eligible(player('SP', saves), 'sp'), true);
    assert.equal(eligible(player('SP', saves), 'rp'), false);
  }
  for (const saves of [2, '2', 10]) {
    assert.equal(eligible(player('SP', saves), 'sp'), true);
    assert.equal(eligible(player('SP', saves), 'rp'), true);
  }
});
