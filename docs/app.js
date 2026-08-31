const CATEGORIES=["R","HR","RBI","SB","AVG","W","SV","K","ERA","WHIP"];
const LOWER_BETTER=new Set(["ERA","WHIP"]);
let data,sort={key:"total_score",dir:"desc"};

const fmt=(key,value)=>["AVG","ERA","WHIP"].includes(key)?Number(value||0).toFixed(3).replace(/^0/,""):Number(value||0).toLocaleString();
const placeClass=p=>p===1?"place place-1":p===2?"place place-2":p===3?"place place-3":"place place-n";
const pointsClass=(pts,values)=>pts===Math.max(...values)?"pts-high":pts===Math.min(...values)?"pts-low":"pts-mid";
const ownerUrl=name=>`?owner=${encodeURIComponent(name)}`;

function applyTheme(){
  const dark=document.documentElement.dataset.theme==="dark";
  document.querySelector("#theme-toggle").setAttribute("aria-pressed",String(dark));
}
document.querySelector("#theme-toggle").addEventListener("click",()=>{
  const next=document.documentElement.dataset.theme==="dark"?"light":"dark";
  document.documentElement.dataset.theme=next;localStorage.setItem("theme",next);applyTheme();
});
applyTheme();

function statValue(row,key){return key==="total_score"?row.total_score:row.stats[key]??0}
function sortedStandings(){return [...data.standings].sort((a,b)=>{
  const av=statValue(a,sort.key),bv=statValue(b,sort.key);
  return sort.dir==="asc"?av-bv:bv-av;
})}

function categoryCell(row,category){
  const all=data.standings.map(r=>r.category_points[category]);
  const pts=row.category_points[category];
  return `<td class="${sort.key===category?'sort-active':''}"><div class="cat-cell"><span class="cat-val">${fmt(category,row.stats[category])}</span><span class="cat-pts ${pointsClass(pts,all)}">${pts.toFixed(1)}</span></div></td>`;
}

function renderDesktop(){
  const headers=CATEGORIES.map(c=>`<th class="sortable ${sort.key===c?'sort-active':''}" data-sort="${c}">${c}<span class="sort-indicator">${sort.key===c?(sort.dir==='asc'?'▲':'▼'):''}</span></th>`).join("");
  const rows=sortedStandings().map(row=>`<tr><td class="col-left"><span class="${placeClass(row.place)}">${row.place}</span></td><td class="col-left"><a class="owner-link" href="${ownerUrl(row.owner)}">${row.owner}</a></td><td class="${sort.key==='total_score'?'sort-active':''}"><span class="score">${row.total_score.toFixed(1)}</span></td>${CATEGORIES.map(c=>categoryCell(row,c)).join('')}</tr>`).join("");
  document.querySelector("#standings-table").innerHTML=`<thead><tr><th class="col-left">Rank</th><th class="col-left">Owner</th><th class="sortable ${sort.key==='total_score'?'sort-active':''}" data-sort="total_score">Score <span class="sort-indicator">${sort.key==='total_score'?(sort.dir==='asc'?'▲':'▼'):''}</span></th>${headers}</tr></thead><tbody>${rows}</tbody>`;
  document.querySelectorAll("[data-sort]").forEach(th=>th.addEventListener("click",()=>changeSort(th.dataset.sort)));
}

function renderMobile(){
  document.querySelector("#mobile-sort").innerHTML=`<option value="total_score">Total score</option>${CATEGORIES.map(c=>`<option value="${c}">${c}</option>`).join('')}`;
  document.querySelector("#mobile-sort").value=sort.key;
  document.querySelector("#mobile-standings").innerHTML=sortedStandings().map((row,i)=>{
    const cats=CATEGORIES.map(c=>`<div class="mob-cat"><label>${c}</label><strong>${fmt(c,row.stats[c])}</strong><span class="cat-pts ${pointsClass(row.category_points[c],data.standings.map(r=>r.category_points[c]))}">${row.category_points[c].toFixed(1)}</span></div>`).join('');
    return `<article class="mob-card"><button class="mob-card-header" aria-expanded="false"><span class="${placeClass(row.place)}">${row.place}</span><span class="owner-link mob-owner">${row.owner}</span><span class="mob-score">${sort.key==='total_score'?row.total_score.toFixed(1):fmt(sort.key,row.stats[sort.key])}</span><svg class="mob-chevron" viewBox="0 0 20 20"><path fill="currentColor" d="m5.2 7.2 4.8 5 4.8-5 1.1 1-5.4 5.7a.75.75 0 0 1-1.1 0L4.1 8.2l1.1-1Z"/></svg></button><div class="mob-detail" hidden><div class="mob-cat-grid">${cats}</div><a class="mob-detail-link" href="${ownerUrl(row.owner)}">View full roster →</a></div></article>`;
  }).join('');
  document.querySelectorAll(".mob-card-header").forEach(button=>button.addEventListener("click",()=>{const detail=button.nextElementSibling;detail.hidden=!detail.hidden;button.setAttribute("aria-expanded",String(!detail.hidden));button.querySelector("svg").style.transform=detail.hidden?"":"rotate(180deg)"}));
}

function changeSort(key){
  if(sort.key===key)sort.dir=sort.dir==="desc"?"asc":"desc";
  else{sort.key=key;sort.dir=LOWER_BETTER.has(key)?"asc":"desc"}
  renderDesktop();renderMobile();
}
document.querySelector("#mobile-sort").addEventListener("change",e=>changeSort(e.target.value));

function totalsRow(section,totals,colspan){
  if(section==="hitting")return `<tr class="totals-row"><td></td><td class="col-left">TEAM TOTAL</td><td>${totals.AB}</td><td>${totals.H}</td><td>${totals.R}</td><td>${totals.HR}</td><td>${totals.RBI}</td><td>${totals.BB}</td><td>${totals.SB}</td><td>${fmt('AVG',totals.AVG)}</td></tr>`;
  return `<tr class="totals-row"><td></td><td class="col-left">TEAM TOTAL</td><td>${totals.IP}</td><td>${totals.W}</td><td>${totals.L}</td><td>${totals.SV}</td><td>${totals.K}</td><td>${totals.P_H}</td><td>${totals.P_BB}</td><td>${totals.P_ER}</td><td>${fmt('ERA',totals.ERA)}</td><td>${fmt('WHIP',totals.WHIP)}</td></tr>`;
}

function renderOwner(name){
  const owner=data.owners.find(o=>o.name===name),standing=data.standings.find(r=>r.owner===name);
  if(!owner){history.replaceState(null,"","./");renderStandings();return}
  document.querySelector("#standings-view").hidden=true;document.querySelector("#owner-view").hidden=false;
  document.querySelector("#owner-name").textContent=`Team ${name}`;document.querySelector("#owner-place").textContent=`${standing.place}${standing.place===1?'st':standing.place===2?'nd':standing.place===3?'rd':'th'} place`;
  document.querySelector("#owner-score").textContent=`${standing.total_score.toFixed(1)} pts`;
  const hitters=owner.players.filter(p=>p.section==="hitting").map(p=>`<tr><td class="col-left slot">${p.slot}</td><td class="col-left player-name">${p.player_name}</td><td>${p.stats.AB}</td><td>${p.stats.H}</td><td>${p.stats.R}</td><td>${p.stats.HR}</td><td>${p.stats.RBI}</td><td>${p.stats.BB}</td><td>${p.stats.SB}</td><td>${fmt('AVG',p.stats.AVG)}</td></tr>`).join('');
  document.querySelector("#hitter-table").innerHTML=`<thead><tr><th class="col-left">Pos</th><th class="col-left">Player</th><th>AB</th><th>H</th><th>R</th><th>HR</th><th>RBI</th><th>BB</th><th>SB</th><th>AVG</th></tr></thead><tbody>${hitters}${totalsRow('hitting',owner.totals,10)}</tbody>`;
  const pitchers=owner.players.filter(p=>p.section==="pitching").map(p=>`<tr><td class="col-left slot">${p.slot}</td><td class="col-left player-name">${p.player_name}</td><td>${p.stats.IP}</td><td>${p.stats.W}</td><td>${p.stats.L}</td><td>${p.stats.SV}</td><td>${p.stats.K}</td><td>${p.stats.H}</td><td>${p.stats.BB}</td><td>${p.stats.ER}</td><td>${fmt('ERA',p.stats.ERA)}</td><td>${fmt('WHIP',p.stats.WHIP)}</td></tr>`).join('');
  document.querySelector("#pitcher-table").innerHTML=`<thead><tr><th class="col-left">Pos</th><th class="col-left">Player</th><th>IP</th><th>W</th><th>L</th><th>SV</th><th>K</th><th>H</th><th>BB</th><th>ER</th><th>ERA</th><th>WHIP</th></tr></thead><tbody>${pitchers}${totalsRow('pitching',owner.totals,12)}</tbody>`;
}

function renderStandings(){document.querySelector("#owner-view").hidden=true;document.querySelector("#standings-view").hidden=false;renderDesktop();renderMobile()}
function leagueMeta(){
  const start=new Date(data.league.start_date+'T00:00:00'),end=new Date(data.league.end_date+'T00:00:00'),today=new Date();
  const day=86400000,elapsed=Math.max(0,Math.min(Math.floor((today-start)/day),Math.round((end-start)/day)+1)),remaining=Math.max(0,Math.ceil((end-today)/day));
  document.querySelector("#days-elapsed").textContent=elapsed;document.querySelector("#days-remaining").textContent=remaining;
  document.querySelector("#header-subtitle").textContent=`Rotisserie standings · ${data.league.start_date} – ${data.league.end_date}`;
  document.querySelector("#as-of").textContent=data.through_date||"No completed games";
  document.querySelector("#status-msg").textContent=`${data.games_counted} MLB games counted${data.through_date?` through ${data.through_date}`:''}`;
}

fetch("data/league.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error(`HTTP ${r.status}`);return r.json()}).then(payload=>{
  data=payload;leagueMeta();const owner=new URLSearchParams(location.search).get("owner");owner?renderOwner(owner):renderStandings();
}).catch(error=>{document.querySelector("#status-msg").textContent=`Could not load standings: ${error.message}`;document.querySelector(".status-dot").style.background="var(--red)"});
