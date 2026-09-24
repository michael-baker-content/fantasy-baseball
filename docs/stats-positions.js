/* Shared position eligibility rules for the player statistics views. */
function playerForStatsSource(player,source,assignments={}){
  if(Object.hasOwn(assignments,String(player.id))){
    const positions=assignments[String(player.id)];
    return {...player,positions,position:positions.join(', ')};
  }
  // Ohtani's displayed position depends on which statistics are being shown.
  if(String(player.id)==="660271")return {...player,position:source==="pitchers"?"SP":"DH"};
  if(source==="pitchers"&&String(player.position||"").trim().toUpperCase()==="P"){
    const starter=eligibleForStatsView(player,"sp"),reliever=eligibleForStatsView(player,"rp");
    if(starter!==reliever)return {...player,position:starter?"SP":"RP"};
  }
  return player;
}
const positionFilters={
  batters:["C","1B","2B","3B","SS","LF","CF","RF","DH"],
  pitchers:["SP","RP"],
  if:["C","1B","2B","3B","SS"],
  of:["LF","CF","RF"],
  sp:["SP"],
  rp:["RP"],
};
function matchesPositionFilter(player,position){
  if(!position)return true;
  if(position==="SP"||position==="RP")return eligibleForStatsView(player,position.toLowerCase());
  if(Array.isArray(player.positions))return player.positions.includes(position);
  return String(player.position||"").trim().toUpperCase()===position;
}
const statsViews={
  batters:{source:"batters",label:"Batters"},
  pitchers:{source:"pitchers",label:"Pitchers"},
  if:{source:"batters",label:"IF"},
  of:{source:"batters",label:"OF"},
  sp:{source:"pitchers",label:"SP"},
  rp:{source:"pitchers",label:"RP"},
};
function eligibleForStatsView(player,view){
  const position=String(player.position||"").trim().toUpperCase();
  const rawStarts=player.stats?.GS;
  const starts=rawStarts===undefined||rawStarts===null||rawStarts===""?NaN:Number(rawStarts);
  if(Array.isArray(player.positions)){
    const positions=player.positions;
    const genericPitcher=positions.includes("P")||positions.includes("TWP");
    switch(view){
      case "if":return positions.some(p=>["C","1B","2B","3B","SS"].includes(p));
      case "of":return positions.some(p=>["LF","CF","RF","OF"].includes(p));
      case "sp":return positions.includes("SP")||(genericPitcher&&starts>1);
      case "rp":return positions.includes("RP")||(genericPitcher&&(Number(player.stats?.SV)>1||(Number.isFinite(starts)&&starts<=1)));
      default:return view==="batters"||view==="pitchers";
    }
  }
  switch(view){
    case "if":return ["C","1B","2B","3B","SS"].includes(position);
    case "of":return ["LF","CF","RF","OF"].includes(position);
    case "sp":return starts>1;
    case "rp":return ["P","SP","RP","TWP"].includes(position)&&(Number(player.stats?.SV)>1||(Number.isFinite(starts)&&starts<=1));
    default:return view==="batters"||view==="pitchers";
  }
}
