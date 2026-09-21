/* Shared position eligibility rules for the player statistics views. */
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
  switch(view){
    case "if":return ["C","1B","2B","3B","SS"].includes(position);
    case "of":return ["LF","CF","RF","OF"].includes(position);
    case "sp":return ["SP","P"].includes(position);
    case "rp":return ["RP","P"].includes(position)||(position==="SP"&&Number(player.stats?.SV)>1);
    default:return view==="batters"||view==="pitchers";
  }
}
