/* Pure helpers shared by desktop and mobile standings. */
const closeCategoryLimits={R:3,HR:1,RBI:3,SB:1,BB:3,AVG:.005,W:1,L:1,SV:1,K:5,ERA:.20,WHIP:.05};
function previousStandings(history,today){
  return [...(history||[])].filter(entry=>entry.date<today).sort((a,b)=>b.date.localeCompare(a.date))[0]||null;
}
function rankMovement(row,baseline){
  const prior=baseline?.standings.find(p=>p.owner===row.owner);
  return prior?.total_score==null||row.total_score==null?null:prior.place-row.place;
}
function closeCategories(row,category,standings){
  const value=row.stats[category],limit=closeCategoryLimits[category];
  if(value==null||limit==null)return [];
  const lower=['L','ERA','WHIP'].includes(category);
  const ordered=standings.filter(other=>other.stats[category]!=null).sort((a,b)=>
    (lower?a.stats[category]-b.stats[category]:b.stats[category]-a.stats[category])||a.owner.localeCompare(b.owner));
  const pairs=ordered.slice(1).map((other,i)=>({a:ordered[i],b:other,gap:Math.abs(ordered[i].stats[category]-other.stats[category])}));
  const ties=pairs.filter(pair=>pair.gap<1e-10);
  // Ties take priority. Otherwise show just the closest pair; equal gaps favor
  // the pair nearer the top of the category, never input or alphabetical order.
  const closest=pairs.reduce((best,pair)=>!best||pair.gap<best.gap-1e-10?pair:best,null);
  const selected=ties.length?ties:closest&&closest.gap<=limit*2+1e-10?[closest]:[];
  const highlighted=new Set(selected.flatMap(pair=>[pair.a.owner,pair.b.owner]));
  if(!highlighted.has(row.owner))return [];
  return standings.filter(other=>other.owner!==row.owner&&highlighted.has(other.owner)&&other.stats[category]!=null)
    .map(other=>({owner:other.owner,gap:Math.abs(value-other.stats[category]),
      ahead:['L','ERA','WHIP'].includes(category)?value<other.stats[category]:value>other.stats[category]}))
    .filter(other=>ties.length?other.gap<1e-10:other.gap<=limit*2+1e-10).sort((a,b)=>a.gap-b.gap||a.owner.localeCompare(b.owner));
}
function categoryHeat(category,gap){return gap<=closeCategoryLimits[category]+1e-10?'hot':'warm'}

function categoryImpact(row,category,rivals,standings){
  const lower=['L','ERA','WHIP'].includes(category);
  let impact='low';
  const active=standings.filter(p=>p.total_score!=null);
  const rank=(scores,owner)=>1+active.filter(p=>scores[p.owner]>scores[owner]).length;
  const original=Object.fromEntries(active.map(p=>[p.owner,p.total_score]));
  for(const rival of rivals){
    const other=standings.find(p=>p.owner===rival.owner);
    if(!other)continue;
    // Test either owner overtaking the other, holding every other category fixed.
    for(const [mover,target] of [[row,other],[other,row]]){
      const values=standings.filter(p=>p.stats[category]!=null&&p.category_points[category]!=null)
        .map(p=>({owner:p.owner,value:p.owner===mover.owner?
          target.stats[category]+(lower?-1:1)*(['AVG','ERA','WHIP'].includes(category)?1e-7:1):p.stats[category]}));
      values.sort((a,b)=>lower?a.value-b.value:b.value-a.value);
      const scores={...original};
      for(let i=0;i<values.length;){
        let end=i+1;
        while(end<values.length&&values[end].value===values[i].value)end++;
        const points=standings.length-(i+end-1)/2;
        for(let j=i;j<end;j++){
          const owner=values[j].owner,p=standings.find(p=>p.owner===owner);
          if(scores[owner]!=null)scores[owner]+=points-p.category_points[category];
        }
        i=end;
      }
      for(const p of active){
        const before=rank(original,p.owner),after=rank(scores,p.owner);
        if(before===after)continue;
        if(before<=3||after<=3)return 'high';
        impact='medium';
      }
    }
  }
  return impact;
}
