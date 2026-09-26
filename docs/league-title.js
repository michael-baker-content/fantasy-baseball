function applyLeagueTitle(league,page=''){
  const name=typeof league?.name==='string'&&league.name.trim()?league.name.trim():'Fantasy Baseball';
  document.querySelectorAll('.header-title').forEach(heading=>{heading.textContent=name});
  document.querySelectorAll('.site-logo').forEach(link=>link.setAttribute('aria-label',`${name} home`));
  document.title=page?`${page} · ${name}`:name;
}
