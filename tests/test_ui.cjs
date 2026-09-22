const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = name => fs.readFileSync(path.join(__dirname, '../docs', name), 'utf8');
const visibleSort = vm.runInNewContext(read('stats-sort.js') + '\nvisibleStatsSort;');
const qualifies = vm.runInNewContext(read('stats-filters.js') + '\nmeetsQualification;');
const injuryBadge = vm.runInNewContext(read('stats-status.js') + '\ninjuredListBadge;');
const ownership = vm.runInNewContext(read('stats-owners.js') + '\nstatsOwnership;');
const matchesOwner = vm.runInNewContext(read('stats-owners.js') + '\nmatchesOwnerStatus;');

test('ownership matches player IDs, deduplicates two-way entries, and supports each filter', () => {
  const lookup = ownership({owners: [
    {name: 'Ali', players: [{player_id: 1}, {player_id: '1'}, {player_id: null}]},
    {name: 'Tim', players: [{player_id: 2}, {player_id: 1}]},
  ]});
  assert.deepEqual(Array.from(lookup.get('1')), ['Ali', 'Tim']);
  assert.equal(lookup.has('null'), false);
  assert.equal(matchesOwner(lookup.get('1'), 'owner:Ali'), true);
  assert.equal(matchesOwner(lookup.get('2'), 'owner:Ali'), false);
  assert.equal(matchesOwner(lookup.get('2'), 'rostered'), true);
  assert.equal(matchesOwner([], 'rostered'), false);
  assert.equal(matchesOwner([], ''), true);
  assert.throws(() => ownership({}), /unavailable/);
});

test('Owner sort resets when its column is hidden on mobile', () => {
  assert.equal(visibleSort({key: 'owner', dir: 1}, 'batters', true, false).key, 'HR');
  assert.equal(visibleSort({key: 'owner', dir: 1}, 'pitchers', true, false).key, 'K');
  assert.equal(visibleSort({key: 'owner', dir: 1}, 'pitchers', false, false).key, 'owner');
});

test('IL badge recognizes official roster codes and descriptions', () => {
  for (const days of [7, 10, 15, 60]) {
    assert.equal(injuryBadge({roster_status_code: `D${days}`}).label, `IL-${days}`);
    assert.equal(injuryBadge({roster_status_code: `IL${days}`}).label, `IL-${days}`);
    assert.equal(injuryBadge({roster_status: `Injured ${days}-Day`}).label, `IL-${days}`);
  }
  assert.equal(injuryBadge({injured_list: true}).label, 'IL');
  assert.equal(injuryBadge({roster_status_code: 'A', roster_status: 'Active', injured_list: false}), null);
  assert.equal(injuryBadge({roster_status_code: 'MIN', roster_status: 'Minors'}), null);
  assert.equal(injuryBadge({}), null);
});

test('AB minimum excludes players from the pool, independent of rate or counting stats', () => {
  const players = [{stats: {AB: 49, HR: 30, AVG: '.900'}}, {stats: {AB: '50', HR: 1, AVG: '.200'}}];
  assert.deepEqual(players.filter(player => qualifies(player, 'batters', 50, 100)), [players[1]]);
  assert.equal(qualifies({stats: {}}, 'batters', 1, 0), false);
  assert.equal(qualifies({stats: {}}, 'batters', 0, 100), true);
});

test('IP minimum compares baseball innings as outs and ignores batting minimum', () => {
  assert.equal(qualifies({stats: {IP: '9.2'}}, 'pitchers', 1000, 10), false);
  assert.equal(qualifies({stats: {IP: '10.0'}}, 'pitchers', 1000, 10), true);
  assert.equal(qualifies({stats: {IP: '10.1'}}, 'pitchers', 1000, 10), true);
  for (const IP of ['', undefined, '10.9']) {
    assert.equal(qualifies({stats: {IP}}, 'pitchers', 0, 10), false);
  }
  assert.equal(qualifies({stats: {}}, 'pitchers', 1000, 0), true);
});

test('hiding supporting columns resets only affected sorts', () => {
  for (const key of ['G', 'AB', 'H', 'IP']) {
    const result = visibleSort({key, dir: 1}, 'batters', true, false);
    assert.equal(result.key, 'HR');
    assert.equal(result.dir, -1);
    assert.equal(visibleSort({key, dir: 1}, 'batters', false, false).key, key);
  }
  assert.equal(visibleSort({key: 'IP', dir: 1}, 'pitchers', true, false).key, 'K');
  assert.equal(visibleSort({key: 'AVG', dir: 1}, 'batters', true, false).dir, 1);
});

test('team filtering resets hidden Team sort and preserves other sorts', () => {
  assert.equal(visibleSort({key: 'team', dir: 1}, 'batters', false, true).key, 'HR');
  assert.equal(visibleSort({key: 'team', dir: 1}, 'pitchers', false, true).key, 'K');
  assert.equal(visibleSort({key: 'team', dir: 1}, 'pitchers', false, false).key, 'team');
  const state = {key: 'ERA', dir: 1};
  const result = visibleSort(state, 'pitchers', true, true);
  assert.equal(result.key, 'ERA');
  assert.equal(result.dir, 1);
  assert.deepEqual(state, {key: 'ERA', dir: 1});
});

function themeHarness(saved, storageBlocked = false) {
  const root = {dataset: {}};
  const attributes = new Map([['aria-pressed', 'false']]);
  const handlers = {};
  const button = {
    setAttribute: (key, value) => attributes.set(key, value),
    removeAttribute: key => attributes.delete(key),
    addEventListener: (key, handler) => { handlers[key] = handler; },
  };
  let ready, stored;
  vm.runInNewContext(read('theme.js'), {
    document: {
      documentElement: root,
      getElementById: () => button,
      addEventListener: (event, handler) => { if (event === 'DOMContentLoaded') ready = handler; },
    },
    localStorage: {
      getItem: () => { if (storageBlocked) throw Error('Storage denied'); return saved; },
      setItem: (key, value) => { if (storageBlocked) throw Error('Storage denied'); stored = value; },
    },
  });
  ready();
  return {root, attributes, click: () => handlers.click(), stored: () => stored};
}

test('shared theme restores preference and updates the action label', () => {
  const theme = themeHarness('dark');
  assert.equal(theme.root.dataset.theme, 'dark');
  assert.equal(theme.attributes.get('aria-label'), 'Switch to Light Mode');
  assert.equal(theme.attributes.has('aria-pressed'), false);
  theme.click();
  assert.equal(theme.root.dataset.theme, 'light');
  assert.equal(theme.attributes.get('aria-label'), 'Switch to Dark Mode');
  assert.equal(theme.stored(), 'light');
});

test('theme switching still works when storage is unavailable', () => {
  const theme = themeHarness(null, true);
  assert.equal(theme.root.dataset.theme, 'light');
  assert.doesNotThrow(() => theme.click());
  assert.equal(theme.root.dataset.theme, 'dark');
  assert.equal(themeHarness('invalid').root.dataset.theme, 'light');
});

function luminance(hex) {
  const rgb = hex.slice(1).match(/../g).map(value => parseInt(value, 16) / 255)
    .map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
  return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
}
function contrast(a, b) {
  const values = [luminance(a), luminance(b)].sort((a, b) => b - a);
  return (values[0] + .05) / (values[1] + .05);
}
test('muted text and selected headings meet normal-text contrast in both themes', () => {
  const css = read('styles.css');
  const tokens = block => Object.fromEntries([...block.matchAll(/--([\w-]+):(#[\da-f]{6})\b/gi)].map(match => [match[1], match[2]]));
  const light = tokens(css.match(/:root\{([^}]+)\}/)[1]);
  const dark = {...light, ...tokens(css.match(/\[data-theme=dark\]\{([^}]+)\}/)[1])};
  for (const theme of [light, dark]) {
    for (const background of ['bg', 'card', 'hover']) {
      assert.ok(contrast(theme.muted, theme[background]) >= 4.5, `muted/${background}`);
    }
    assert.ok(contrast(theme.faint, theme.card) >= 4.5, 'footer');
    assert.ok(contrast(theme['sort-text'], theme.hover) >= 4.5, 'sorted heading');
    assert.ok(contrast(theme.focus, theme.card) >= 3, 'focus indicator');
  }
});
