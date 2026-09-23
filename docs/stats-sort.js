const supportingColumns = new Set(['G', 'AB', 'H', 'IP']);
const playerNameCollator = new Intl.Collator('en', {sensitivity:'base'});

function playerNameParts(name){
  const parts=String(name||'').trim().split(/\s+/);
  const first=parts.length>1?parts.shift():'';
  // Keep compound surnames together; suffixes do not precede given names.
  const suffix=parts.length>1&&/^(jr\.?|sr\.?|II|III|IV)$/i.test(parts.at(-1))?parts.pop():'';
  return [parts.join(' '),first,suffix];
}
function comparePlayerNames(a,b){
  const left=playerNameParts(a.name),right=playerNameParts(b.name);
  for(let index=0;index<left.length;index++){
    const result=playerNameCollator.compare(left[index],right[index]);
    if(result)return result;
  }
  return 0;
}

function visibleStatsSort(state, source, narrow, teamSelected) {
  const hidden = (narrow && (supportingColumns.has(state.key) || state.key === 'owner')) ||
    (teamSelected && state.key === 'team');
  return hidden ? {key: source === 'batters' ? 'HR' : 'K', dir: -1} : {...state};
}
