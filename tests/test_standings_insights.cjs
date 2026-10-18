const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const context={};
vm.createContext(context);
vm.runInContext(fs.readFileSync(require('node:path').join(__dirname,'../docs/standings-insights.js'),'utf8'),context);
test('baseline excludes today and carries the previous close through idle days',()=>{
  const history=[{date:'2026-10-15'},{date:'2026-10-17'}];
  assert.equal(context.previousStandings(history,'2026-10-17').date,'2026-10-15');
  assert.equal(context.previousStandings(history,'2026-10-18').date,'2026-10-17');
  assert.equal(context.previousStandings(history,'2026-10-14'),null);
});
test('movement handles ties and missing scores',()=>{
  const baseline={standings:[{owner:'A',place:4,total_score:50}]};
  assert.equal(context.rankMovement({owner:'A',place:2,total_score:55},baseline),2);
  assert.equal(context.rankMovement({owner:'A',place:2,total_score:null},baseline),null);
});
test('close gaps include ties, exclude nulls, and reverse ERA direction',()=>{
  const a={owner:'A',stats:{HR:3,ERA:2}};
  const rows=[a,{owner:'B',stats:{HR:4,ERA:2.2}},{owner:'C',stats:{HR:null,ERA:null}},
    {owner:'D',stats:{HR:3,ERA:3}}];
  assert.equal(context.closeCategories(a,'HR',rows).length,1);
  const rivals=context.closeCategories(a,'ERA',rows);
  assert.equal(rivals.length,1);
  assert.equal(rivals[0].ahead,true);
});
test('dense category highlights only two owners unless tied',()=>{
  const rows=Array.from({length:8},(_,i)=>({owner:String(i),stats:{HR:i}}));
  assert.equal(rows.filter(row=>context.closeCategories(row,'HR',rows).length).length,2);
  rows.forEach(row=>row.stats.HR=2);
  assert.equal(rows.filter(row=>context.closeCategories(row,'HR',rows).length).length,8);
});
test('icons distinguish very close and moderate gaps',()=>{
  assert.equal(context.categoryHeat('HR',1),'hot');
  assert.equal(context.categoryHeat('HR',2),'warm');
  const a={owner:'A',stats:{HR:3}};
  assert.equal(context.closeCategories(a,'HR',[a,{owner:'B',stats:{HR:6}}]).length,0);
});
test('impact distinguishes top-three, lower-place, and no place movement',()=>{
  const make=scores=>scores.map((score,i)=>({owner:String(i),total_score:score,
    stats:{HR:10-i*2},category_points:{HR:5-i}}));
  let rows=make([100,80,60,40,20]);
  assert.equal(context.categoryImpact(rows[3],'HR',[{owner:'4'}],rows),'low');
  rows=make([100,80,60,21,20]);
  assert.equal(context.categoryImpact(rows[3],'HR',[{owner:'4'}],rows),'medium');
  rows=make([100,99,60,40,20]);
  assert.equal(context.categoryImpact(rows[0],'HR',[{owner:'1'}],rows),'high');
});
