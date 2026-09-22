function numeric(key,value){
  if(value===null||value===undefined||String(value).trim()==="")return null;
  if(key==="IP"){
    const match=String(value).match(/^(\d+)(?:\.([012]))?$/);
    return match?Number(match[1])*3+Number(match[2]||0):null;
  }
  const number=Number(value);return Number.isFinite(number)?number:null;
}

function meetsQualification(player,source,minAB,minIP){
  const minimum=source==="batters"?minAB:minIP*3;
  if(minimum===0)return true;
  const value=numeric(source==="batters"?"AB":"IP",player.stats?.[source==="batters"?"AB":"IP"]);
  return value!==null&&value>=minimum;
}
