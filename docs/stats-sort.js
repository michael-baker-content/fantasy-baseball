const supportingColumns = new Set(['G', 'AB', 'H', 'IP']);

function visibleStatsSort(state, source, narrow, teamSelected) {
  const hidden = (narrow && supportingColumns.has(state.key)) ||
    (teamSelected && state.key === 'team');
  return hidden ? {key: source === 'batters' ? 'HR' : 'K', dir: -1} : {...state};
}
