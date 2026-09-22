function statsOwnership(league){
  if(!Array.isArray(league.owners))throw new Error("Roster ownership data is unavailable.");
  const byPlayer=new Map();
  for(const owner of league.owners){
    for(const player of owner.players){
      if(player.player_id===null||player.player_id===undefined)continue;
      const id=String(player.player_id),names=byPlayer.get(id)||[];
      if(!names.includes(owner.name))names.push(owner.name);
      byPlayer.set(id,names);
    }
  }
  return byPlayer;
}
function matchesOwnerStatus(owners,status){
  return !status||(status==="rostered"?owners.length>0:owners.includes(status.slice(6)));
}
