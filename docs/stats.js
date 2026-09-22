const columns={batters:["G","AB","H","R","HR","RBI","SB","BB","AVG"],pitchers:["G","IP","W","L","SV","K","ERA","WHIP"]};
const narrowStats=window.matchMedia('(max-width: 640px)');
const teamAbbreviations={"Arizona Diamondbacks":"AZ","Atlanta Braves":"ATL","Boston Red Sox":"BOS","Chicago Cubs":"CHC","Chicago White Sox":"CWS","Cleveland Guardians":"CLE","Houston Astros":"HOU","Los Angeles Dodgers":"LAD","Milwaukee Brewers":"MIL","New York Yankees":"NYY","Philadelphia Phillies":"PHI","San Diego Padres":"SD","Tampa Bay Rays":"TB","Texas Rangers":"TEX"};
const teamLabel=player=>player.team_abbreviation||teamAbbreviations[player.team]||player.team;
const states=Object.fromEntries(Object.entries(statsViews).map(([view,details])=>[view,{key:details.source==="batters"?"HR":"K",dir:-1}]));
let ranges=[],group="batters";
let ownership=new Map();
const pageSize=25;
let visibleLimit=pageSize;
let qualificationMinimums=[0,0];
const el=id=>document.getElementById(id);
el("stats-filters-toggle").addEventListener("click",()=>{
  const panel=el("stats-filters-panel");
  panel.hidden=!panel.hidden;
  el("stats-filters-toggle").setAttribute("aria-expanded",String(!panel.hidden));
});
const infoDialog=el("stats-info-dialog");
el("stats-info-open").addEventListener("click",()=>infoDialog.showModal());
el("stats-info-close").addEventListener("click",()=>infoDialog.close());
infoDialog.addEventListener("click",event=>{
  if(event.target!==infoDialog)return;
  const bounds=infoDialog.getBoundingClientRect();
  if(event.clientX<bounds.left||event.clientX>bounds.right||event.clientY<bounds.top||event.clientY>bounds.bottom)infoDialog.close();
});
infoDialog.addEventListener("close",()=>el("stats-info-open").focus({preventScroll:true}));
const escapeHtml=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const normalize=value=>String(value).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
function format(key,value){
  const number=numeric(key,value);if(number===null)return "—";
  if(key==="IP")return `${Math.floor(number/3)}.${number%3}`;
  if(key==="AVG")return number.toFixed(3).replace(/^0/,"");
  if(key==="ERA"||key==="WHIP")return number.toFixed(3);
  return number.toLocaleString();
}
function playerNameCell(player,rosterDate){
  const badge=injuredListBadge(player);
  const description=badge?`${badge.description}; roster as of ${rosterDate}`:"";
  return `${escapeHtml(player.name)}${badge?` <span class="stats-il-badge" title="${escapeHtml(description)}"><span aria-hidden="true">${badge.label}</span><span class="sr-only">${escapeHtml(description)}</span></span>`:""}`;
}
function render(keepPage=false){
  if(keepPage!==true)visibleLimit=pageSize;
  const range=ranges[Number(el("stats-range").value)];if(!range)return;
  const minimumInputs=[el("stats-min-ab"),el("stats-min-ip")];
  let valid=true;
  minimumInputs.forEach(input=>{const ok=input.validity.valid;input.setAttribute("aria-invalid",String(!ok));valid=valid&&ok});
  el("stats-qualification-error").hidden=valid;
  if(valid)qualificationMinimums=minimumInputs.map(input=>Number(input.value||0));
  const [minAB,minIP]=qualificationMinimums;
  const state=states[group],query=normalize(el("stats-search").value.trim()),team=el("stats-team").value;
  const ownerStatus=el("stats-owner").value;
  const view=statsViews[group],source=range[view.source].map(player=>({...playerForStatsSource(player,view.source),owners:ownership.get(String(player.id))||[],owner:(ownership.get(String(player.id))||[]).join(", ")}));
  Object.assign(state,visibleStatsSort(state,view.source,narrowStats.matches,Boolean(team)));
  const eligible=source.filter(player=>eligibleForStatsView(player,group)&&matchesOwnerStatus(player.owners,ownerStatus));
  const position=el("stats-position").value;
  const rows=eligible.filter(player=>meetsQualification(player,view.source,minAB,minIP)&&matchesPositionFilter(player,position)&&(!team||player.team===team)&&normalize(player.name).includes(query));
  rows.sort((a,b)=>{
    const text=["name","team","position","owner"].includes(state.key);
    const av=text?(state.key==="team"?teamLabel(a):a[state.key]||null):numeric(state.key,a.stats[state.key]),bv=text?(state.key==="team"?teamLabel(b):b[state.key]||null):numeric(state.key,b.stats[state.key]);
    if(av===null||bv===null)return av===bv?a.name.localeCompare(b.name):av===null?1:-1;
    return (text?av.localeCompare(bv):av-bv)*state.dir||a.name.localeCompare(b.name);
  });
  const keys=["name","position",...(!team?["team"]:[]),"owner",...columns[view.source]];
  el("player-stats-table").querySelector("caption").textContent=`${view.label} statistics, ${range.start} through ${range.through}`;
  el("player-stats-table").querySelector("thead").innerHTML=`<tr>${keys.map(key=>`<th scope="col" class="${key==="owner"?"stats-owner-cell":supportingColumns.has(key)?"stats-supporting":""}" aria-sort="${state.key===key?(state.dir===1?"ascending":"descending"):"none"}"><button type="button" data-sort="${key}"${key==="position"?' aria-label="Primary position"':""}>${key==="name"?"Player":key==="team"?"Team":key==="owner"?"Owner":key==="position"?"Pos.":key}${state.key===key?(state.dir===1?" ▲":" ▼"):""}</button></th>`).join("")}</tr>`;
  el("player-stats-table").querySelector("tbody").innerHTML=rows.slice(0,visibleLimit).map(player=>`<tr><td title="${escapeHtml(player.name)}">${playerNameCell(player,range.roster_date)}</td><td class="stats-position-cell">${escapeHtml(player.position||"—")}</td>${!team?`<td class="stats-team-cell" title="${escapeHtml(player.team)}">${escapeHtml(teamLabel(player))}</td>`:""}<td class="stats-owner-cell">${escapeHtml(player.owner||"Unrostered")}</td>${columns[view.source].map(key=>`<td class="${supportingColumns.has(key)?"stats-supporting":""}">${format(key,player.stats[key])}</td>`).join("")}</tr>`).join("");
  el("stats-dates").textContent=`Statistics: ${range.start} through ${range.through} (inclusive). Current organizations as of ${range.roster_date}.`;
  const qualification=view.source==="batters"?(minAB?` · Minimum ${minAB} AB`:""):(minIP?` · Minimum ${minIP} IP`:"");
  el("stats-count").textContent=`Showing ${Math.min(visibleLimit,rows.length)} of ${rows.length} matching ${view.label} players${ownerStatus?` · ${el("stats-owner").selectedOptions[0].textContent}`:""}${position?` · Position: ${position}`:""}${qualification}`;
  el("stats-show-more").hidden=visibleLimit>=rows.length;
  el("stats-show-more").textContent=`Show ${Math.min(pageSize,Math.max(0,rows.length-visibleLimit))} more`;
  el("stats-empty").hidden=rows.length!==0;
  el("stats-empty").textContent=["sp","rp"].includes(group)&&source.some(player=>player.stats.GS===undefined||player.stats.GS==="")?"Starts data is unavailable for some players in this range. Refresh its published data to populate the pitching tabs.":["if","of"].includes(group)&&source.some(player=>!player.position)?"Position information is missing for some players in this range. Refresh its published data to populate the position tabs.":"No players match these filters.";
}
function refreshPositions(){
  const range=ranges[Number(el("stats-range").value)];if(!range)return;
  const select=el("stats-position"),previous=select.value;
  const positions=positionFilters[group];
  select.replaceChildren(new Option("All positions",""),...positions.map(position=>new Option(position,position)));
  if(positions.includes(previous))select.value=previous;
}
function selectRange(){
  const range=ranges[Number(el("stats-range").value)],previous=el("stats-team").value;
  el("stats-team").replaceChildren(new Option("All teams",""),...range.teams.map(team=>new Option(team,team)));
  if(range.teams.includes(previous))el("stats-team").value=previous;
  refreshPositions();
  render();
}
function selectTab(button){
  group=button.dataset.group;
  document.querySelectorAll("[role=tab]").forEach(tab=>{const active=tab===button;tab.setAttribute("aria-selected",String(active));tab.tabIndex=active?0:-1});
  el("stats-panel").setAttribute("aria-labelledby",button.id);refreshPositions();render();
}
document.querySelectorAll("[role=tab]").forEach(button=>{
  button.addEventListener("click",()=>selectTab(button));
  button.addEventListener("keydown",event=>{
    if(!["ArrowLeft","ArrowRight","Home","End"].includes(event.key))return;
    event.preventDefault();const tabs=[...document.querySelectorAll("[role=tab]")],index=tabs.indexOf(button);
    const target=event.key==="Home"?tabs[0]:event.key==="End"?tabs[tabs.length-1]:tabs[(index+(event.key==="ArrowRight"?1:-1)+tabs.length)%tabs.length];
    selectTab(target);target.focus();
  });
});
el("player-stats-table").addEventListener("click",event=>{
  const button=event.target.closest("button[data-sort]");if(!button)return;
  const state=states[group],key=button.dataset.sort;
  state.dir=state.key===key?-state.dir:["name","team","position","owner","L","ERA","WHIP"].includes(key)?1:-1;
  state.key=key;render();el("player-stats-table").querySelector(`button[data-sort="${key}"]`).focus({preventScroll:true});
});
el("stats-range").addEventListener("change",selectRange);
el("stats-team").addEventListener("change",render);
el("stats-owner").addEventListener("change",render);
el("stats-position").addEventListener("change",render);
el("stats-search").addEventListener("input",render);
el("stats-min-ab").addEventListener("input",render);
el("stats-min-ip").addEventListener("input",render);
narrowStats.addEventListener("change",()=>{
  const focusedSort=document.activeElement?.closest('button[data-sort]');
  render();
  if(focusedSort)el("player-stats-table").querySelector(`button[data-sort="${states[group].key}"]`)?.focus({preventScroll:true});
});
el("stats-show-more").addEventListener("click",()=>{
  visibleLimit+=pageSize;render(true);
  if(el("stats-show-more").hidden)el("player-stats-table").closest(".stats-table-wrap").focus({preventScroll:true});
});
Promise.all([fetch("data/player-stats.json",{cache:"no-store"}).then(response=>{
  if(response.status===404)throw new Error("Player statistics have not been published yet.");
  if(!response.ok)throw new Error("Player statistics could not be loaded. Please try again later.");
  return response.json();
}),fetch("data/league.json",{cache:"no-store"}).then(response=>{
  if(!response.ok)throw new Error("Roster ownership data could not be loaded. Please try again later.");
  return response.json();
})]).then(([payload,league])=>{
  if(!Array.isArray(payload.ranges)||!payload.ranges.length)throw new Error("Player statistics have not been published yet.");
  ranges=payload.ranges;
  ownership=statsOwnership(league);
  el("stats-owner").replaceChildren(new Option("All Players",""),new Option("Rostered Players","rostered"),...league.owners.map(owner=>new Option(owner.name,`owner:${owner.name}`)));
  el("stats-range").replaceChildren(...ranges.map((range,index)=>new Option(range.label,index)));
  el("stats-status").textContent="";el("stats-content").hidden=false;selectRange();
}).catch(error=>{el("stats-content").hidden=true;el("stats-status").textContent=error.message});
