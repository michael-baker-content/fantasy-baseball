function injuredListBadge(player){
  const code=String(player.roster_status_code||"").trim().toUpperCase();
  const description=String(player.roster_status||"");
  const codedDays=code.match(/^(?:D|DL|IL)(7|10|15|60)$/);
  const injured=player.injured_list===true||Boolean(codedDays)||/injur|disabled/i.test(description);
  if(!injured)return null;
  const days=codedDays?.[1]||description.match(/\b(7|10|15|60)[ -]?day\b/i)?.[1];
  return {label:days?`IL-${days}`:'IL',description:days?`${days}-Day Injured List`:'Injured List'};
}
