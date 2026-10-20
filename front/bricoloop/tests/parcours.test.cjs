const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const {join}=require('node:path');
const {JSDOM}=require('jsdom');
const dir=join(__dirname,'..');
const tool={id:1,ownerId:1,name:'Perceuse Bosch',category:'Perçage',description:'750 W',etat:null,status:'available'};
const users=[{id:1,firstName:'Rida',district:'Centre'},{id:2,firstName:'Marc',district:'Gare'}];
async function settle(){for(let i=0;i<8;i++)await new Promise(setImmediate);}
async function page(handler=()=>null){
 const dom=new JSDOM(readFileSync(join(dir,'bricoloop-catalogue.html'),'utf8'),{url:'http://localhost:8000/web/bricoloop-catalogue.html',runScripts:'outside-only'});
 const w=dom.window;const calls=[];
 w.HTMLDialogElement.prototype.showModal=function(){this.open=true};
 w.HTMLDialogElement.prototype.close=function(){this.open=false};
 w.fetch=async(url,options={})=>{
  const path=new URL(url).pathname;calls.push({path,url,...options});
  const custom=await handler(path,options);
  if(custom)return {ok:custom.status<400,status:custom.status,json:async()=>custom.body};
  const body=path==='/api/users'?users:path==='/api/tools'?[tool]:path==='/api/tools/1'?{...tool,owner:users[0]}:[];
  return {ok:true,status:200,json:async()=>body};
 };
 w.eval(readFileSync(join(dir,'catalogue.js'),'utf8'));await settle();
 return {w,calls,close:()=>w.close(),change(id,value){w.document.getElementById(id).value=value;w.document.getElementById(id).dispatchEvent(new w.Event('change'));}};
}
test('profil → catalogue → fiche → demande et message de confirmation',async()=>{
 const p=await page((path,o)=>o.method==='POST'&&path.endsWith('/loans')?{status:201,body:{id:42,status:'pending'}}:null);
 try{
  assert.match(p.w.document.getElementById('catalogue').textContent,/Perceuse Bosch/);
  p.change('profile','2');await settle();
  p.w.document.querySelector('#catalogue button').click();await settle();
  assert.match(p.w.document.getElementById('detailText').textContent,/Rida/);
  assert.equal(p.w.document.getElementById('loanForm').hidden,false);
  p.w.document.getElementById('loanStart').value='2030-01-01';p.w.document.getElementById('loanEnd').value='2030-01-02';
  p.w.document.getElementById('loanForm').dispatchEvent(new p.w.Event('submit',{cancelable:true}));await settle();
  const post=p.calls.find(c=>c.method==='POST');
  assert.equal(post.headers['X-User-Id'],'2');assert.deepEqual(JSON.parse(post.body),{startDate:'2030-01-01',endDate:'2030-01-02'});
  assert.match(p.w.document.getElementById('loanMessage').textContent,/en attente/);
 }finally{p.close()}
});
test('erreur 409 de l’API affichée en clair',async()=>{
 const p=await page((path,o)=>o.method==='POST'?{status:409,body:{detail:'Les dates chevauchent un prêt accepté'}}:null);
 try{
  p.change('profile','2');await settle();p.w.document.querySelector('#catalogue button').click();await settle();
  p.w.document.getElementById('loanStart').value='2030-01-01';p.w.document.getElementById('loanEnd').value='2030-01-02';
  p.w.document.getElementById('loanForm').dispatchEvent(new p.w.Event('submit',{cancelable:true}));await settle();
  assert.match(p.w.document.getElementById('loanMessage').textContent,/chevauchent/);
  assert.equal(p.w.document.getElementById('submitLoan').disabled,false);
 }finally{p.close()}
});
test('le propriétaire ne peut pas demander son outil',async()=>{
 const p=await page();try{p.change('profile','1');await settle();p.w.document.querySelector('#catalogue button').click();await settle();assert.equal(p.w.document.getElementById('loanForm').hidden,true);assert.match(p.w.document.getElementById('loanMessage').textContent,/propre outil/)}finally{p.close()}
});
test('panne API : aucune donnée statique affichée',async()=>{
 const p=await page(path=>path==='/api/tools'?{status:503,body:{detail:'Base indisponible'}}:null);
 try{assert.equal(p.w.document.getElementById('catalogue').children.length,0);assert.match(p.w.document.getElementById('notice').textContent,/Impossible/)}finally{p.close()}
});
test('recherche et catégorie envoyées à l’API',async()=>{
 const p=await page();try{
  p.change('category','Jardinage');
  p.w.document.getElementById('search').value='Bosch';p.w.document.getElementById('search').dispatchEvent(new p.w.Event('input'));await settle();
  const requests=p.calls.filter(c=>c.path==='/api/tools');assert.ok(requests.length>=3);const last=new URL(requests.at(-1).url);assert.equal(last.searchParams.get('q'),'Bosch');assert.equal(last.searchParams.get('category'),'Jardinage');
 }finally{p.close()}
});
test('noter un emprunteur après retour et afficher la note',async()=>{
 let rating=null;
 const p=await page((path,o)=>{
  if(path==='/api/loans/received')return {status:200,body:[{id:3,toolId:1,borrowerId:2,toolName:'Perceuse Bosch',borrower:users[1],startDate:'2026-01-01',endDate:'2026-01-02',status:'returned',rating}]};
  if(path==='/api/loans/3/rating'){rating=JSON.parse(o.body).score;return {status:201,body:{id:1,loanId:3,score:rating}}}
 });
 try{
  p.change('profile','1');await settle();const form=p.w.document.querySelector('#receivedLoans form');assert.ok(form);
  form.querySelector('select').value='5';form.dispatchEvent(new p.w.Event('submit',{cancelable:true}));await settle();
  assert.equal(rating,5);assert.match(p.w.document.getElementById('receivedLoans').textContent,/5\/5/);assert.equal(p.w.document.querySelector('#receivedLoans form'),null);
 }finally{p.close()}
});
test('historique visible dans la fiche du propriétaire',async()=>{
 const p=await page(path=>path==='/api/tools/1/history'?{status:200,body:[{id:4,borrower:users[1],startDate:'2026-01-01',endDate:'2026-01-02',status:'returned',rating:4}]}:null);
 try{p.change('profile','1');await settle();p.w.document.querySelector('#catalogue button').click();await settle();assert.equal(p.w.document.getElementById('historyPanel').hidden,false);assert.match(p.w.document.getElementById('toolHistory').textContent,/Marc/);assert.match(p.w.document.getElementById('toolHistory').textContent,/4\/5/);p.change('profile','2');await settle();assert.equal(p.w.document.getElementById('historyPanel').hidden,true)}finally{p.close()}
});

test('erreur 400 du catalogue conserve le message et le champ de l’API',async()=>{
 const p=await page(path=>path==='/api/tools'?{status:400,body:{detail:[{field:'category',message:'Catégorie inconnue'}]}}:null);
 try{const message=p.w.document.getElementById('notice').textContent;assert.match(message,/category/);assert.match(message,/Catégorie inconnue/)}finally{p.close()}
});
