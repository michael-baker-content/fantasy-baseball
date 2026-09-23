const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../docs/stats-positions.js'), 'utf8');
const eligible = vm.runInNewContext(source + '\neligibleForStatsView;');
const filters = vm.runInNewContext(source + '\npositionFilters;');
const matches = vm.runInNewContext(source + '\nmatchesPositionFilter;');
const forSource = vm.runInNewContext(source + '\nplayerForStatsSource;');
const player = (position, saves = 0, starts = 0) => ({position, stats: {SV: saves, GS: starts}});

test('Ohtani displays by statistics source without changing saved data or pitching eligibility', () => {
  const original = {id: 660271, ...player('TWP', 0, 3)};
  const batter = forSource(original, 'batters');
  const pitcher = forSource(original, 'pitchers');
  assert.equal(batter.position, 'DH');
  assert.equal(matches(batter, 'DH'), true);
  assert.equal(eligible(batter, 'if'), false);
  assert.equal(eligible(batter, 'of'), false);
  assert.equal(pitcher.position, 'SP');
  assert.equal(matches(pitcher, 'SP'), true);
  assert.equal(matches(pitcher, 'RP'), false);
  assert.equal(eligible(forSource({...original, stats: {GS: 1, SV: 0}}, 'pitchers'), 'rp'), true);
  assert.equal(original.position, 'TWP');
  assert.equal(forSource({...original, id: '660271'}, 'batters').position, 'DH');
  const other = {id: 123, ...player('TWP')};
  assert.equal(forSource(other, 'batters'), other);
});

test('generic pitchers display their exclusive role for the selected range', () => {
  for (const [starts, saves, expected] of [[3,0,'SP'], [0,3,'RP'], [1,0,'RP'], [0,0,'RP'], [3,2,'P']]) {
    const original = player('P', saves, starts);
    const displayed = forSource(original, 'pitchers');
    assert.equal(displayed.position, expected);
    assert.equal(original.position, 'P');
    for (const view of ['sp', 'rp']) assert.equal(eligible(displayed, view), eligible(original, view));
  }
  assert.equal(forSource({position: 'P', stats: {}}, 'pitchers').position, 'P');
  assert.equal(forSource(player('P', 0, 3), 'batters').position, 'P');
  assert.equal(forSource(player('RP', 0, 3), 'pitchers').position, 'RP');
});

test('position menus have only relevant positions in the requested order', () => {
  const expected = {
    batters: ['C','1B','2B','3B','SS','LF','CF','RF','DH'],
    pitchers: ['SP','RP'], if: ['C','1B','2B','3B','SS'],
    of: ['LF','CF','RF'], sp: ['SP'], rp: ['RP'],
  };
  for (const [view, positions] of Object.entries(expected)) {
    assert.deepEqual(Array.from(filters[view]), positions);
  }
});

test('pitching position filters use statistics, not generic P labels', () => {
  assert.equal(matches(player('P', 0, 3), 'SP'), true);
  assert.equal(matches(player('P', 0, 3), 'RP'), false);
  assert.equal(matches(player('P', 0, 0), 'RP'), true);
  assert.equal(matches(player('P', 2, 3), 'SP'), true);
  assert.equal(matches(player('P', 2, 3), 'RP'), true);
  assert.equal(matches(player('CF'), 'CF'), true);
  assert.equal(matches(player('LF'), 'CF'), false);
  assert.equal(matches(player('TWP'), ''), true);
});

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
test('primary DH and missing positions are excluded from fielding tabs', () => {
  for (const position of ['DH', '', undefined]) {
    assert.equal(eligible(player(position), 'batters'), true);
    for (const view of ['if', 'of']) assert.equal(eligible(player(position), view), false);
  }
  assert.equal(eligible(player(''), 'pitchers'), true);
});
test('SP requires at least two starts regardless of position label', () => {
  for (const position of ['P', 'SP', 'RP', 'TWP', '']) {
    for (const starts of [0, 1, '1', '', undefined]) {
      assert.equal(eligible(player(position, 0, starts), 'sp'), false);
    }
    for (const starts of [2, '2', 10]) {
      assert.equal(eligible(player(position, 0, starts), 'sp'), true);
    }
  }
  assert.equal(eligible({position: 'SP', stats: {}}, 'sp'), false);
});
test('starters need at least two saves to also qualify for RP', () => {
  for (const position of ['P', 'SP', 'RP', 'TWP']) {
    for (const saves of [0, 1, '1', '']) {
      assert.equal(eligible(player(position, saves, 10), 'rp'), false);
    }
    for (const saves of [2, '2', 10]) {
      assert.equal(eligible(player(position, saves, 10), 'rp'), true);
    }
  }
  assert.equal(eligible({position: 'RP', stats: {}}, 'rp'), false);
});
test('pitchers meeting neither threshold fall into RP; both thresholds qualify for both', () => {
  const both = player('P', 2, 2), neither = player('P', 1, 1);
  for (const view of ['sp', 'rp']) {
    assert.equal(eligible(both, view), true);
  }
  assert.equal(eligible(neither, 'sp'), false);
  assert.equal(eligible(neither, 'rp'), true);
  assert.equal(eligible(player('P', 0, 0), 'rp'), true);
  assert.equal(eligible(neither, 'pitchers'), true);
});
test('missing starts are not silently treated as zero starts', () => {
  for (const GS of [undefined, null, '', 'unknown']) {
    const row = {position: 'P', stats: {GS, SV: 0}};
    assert.equal(eligible(row, 'sp'), false);
    assert.equal(eligible(row, 'rp'), false);
    assert.equal(eligible(row, 'pitchers'), true);
  }
});

test('RP excludes incidental position-player pitching but retains designated two-way players', () => {
  for (const position of ['C','1B','2B','3B','SS','LF','CF','RF','OF','DH','']) {
    for (const saves of [0, 2]) {
      const row = player(position, saves, 0);
      assert.equal(eligible(row, 'rp'), false);
      assert.equal(matches(row, 'RP'), false);
      assert.equal(eligible(row, 'pitchers'), true);
    }
  }
  assert.equal(eligible(player('TWP', 0, 0), 'rp'), true);
  assert.equal(eligible(player('TWP', 0, 3), 'rp'), false);
});
