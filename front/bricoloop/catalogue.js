
'use strict';
const API_URL=location.port==='5500'?'http://localhost:8000':location.origin;
const statusNames={available:'Disponible',lent:'Prêté',unavailable:'Indisponible'};
const iconByCat={'Perçage':'🛠️','Jardinage':'🌿','Peinture':'🖌️','Nettoyage':'🧽','Mesure':'📏','Autre':'🧰'};
const $=id=>document.getElementById(id);
let tools=[];
function el(tag,cls,text){const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=String(text);return x}
function render(){
 const q=$('search').value.trim().toLocaleLowerCase('fr');const cat=$('category').value;
 const shown=tools.filter(t=>(!cat||t.category===cat)&&(!q||[t.name,t.description].some(v=>String(v||'').toLocaleLowerCase('fr').includes(q)))).sort((a,b)=>Number(b.status==='available')-Number(a.status==='available'));
 $('count').textContent=`${shown.length} outil${shown.length!==1?'s':''} trouvé${shown.length!==1?'s':''} · les disponibles sont affichés en premier`;
 const root=$('catalogue');root.replaceChildren();
 if(!shown.length){const empty=el('div','empty');empty.append(el('div','emoji','🔎'),el('strong','',(tools.length||q||cat)?'Aucun outil trouvé':'Aucun outil pour le moment'),el('p','',(tools.length||q||cat)?'Essayez une autre recherche ou catégorie.':'Aucun outil n’est actuellement proposé.'));root.append(empty);return}
 for(const tool of shown){
  const card=el('article','tool');const illustration=el('div','illustration');illustration.append(el('span','emoji',iconByCat[tool.category]||'🧰'),el('span','tag',tool.category||'Autre'));
  const d=el('div','details');d.append(el('h3','',tool.name),el('div','category',tool.description||'Un outil à partager'),el('p','',`État : ${tool.etat||'Non renseigné'}`));
  const bottom=el('div','bottom');const status=el('div','status '+tool.status);status.append(el('span','dot'),document.createTextNode(statusNames[tool.status]||tool.status));
  const btn=el('button','smallbtn','Voir le détail →');btn.type='button';btn.addEventListener('click',()=>loadDetail(tool.id));bottom.append(status,btn);d.append(bottom);card.append(illustration,d);root.append(card)
 }
}
function fillCategories(){const previous=$('category').value;$('category').replaceChildren(new Option('Toutes les catégories',''));for(const c of ['Perçage','Jardinage','Peinture','Nettoyage','Mesure','Autre'])$('category').add(new Option(c,c));$('category').value=previous}
$('search').addEventListener('input',loadTools);$('category').addEventListener('change',loadTools);$('closeDialog').addEventListener('click',()=>$('details').close());

let currentDetail=null;
async function loadDetail(id){
 currentDetail=null;$('loanForm').hidden=true;$('loanMessage').textContent='';$('editEtatForm').hidden=true;$('etatMessage').textContent='';
 $('detailName').textContent='Chargement…';$('detailText').textContent='';if(!$('details').open)$('details').showModal();
 try{
  const response=await fetch(`${API_URL}/api/tools/${id}`);
  if(!response.ok)throw new Error(response.status===404?'Outil introuvable':`Erreur HTTP ${response.status}`);
  const tool=await response.json();
  if(!$('details').open)return;
  currentDetail=tool;updateEtatEditor();
  $('detailName').textContent=tool.name;
  $('detailText').textContent=`Catégorie : ${tool.category}\nStatut : ${statusNames[tool.status]||tool.status}\nÉtat : ${tool.etat||'Non renseigné'}\nDescription : ${tool.description||'Aucune description'}\nPropriétaire : ${tool.owner.firstName}\nQuartier : ${tool.owner.district}`;
 }catch(error){$('detailName').textContent='Fiche indisponible';$('detailText').textContent=error.message}
}
let catalogueRequest=0;
async function loadTools(){
 const request=++catalogueRequest;
 const button=$('refresh');button.disabled=true;button.textContent='Connexion…';
 $('source').textContent='Chargement…';
 try{
  const params=new URLSearchParams();if($('category').value)params.set('category',$('category').value);if($('search').value.trim())params.set('q',$('search').value.trim());
  const response=await fetch(`${API_URL}/api/tools${params.size?'?'+params:''}`,{headers:{Accept:'application/json'}});
  if(!response.ok)throw new Error('HTTP '+response.status);
  const data=await response.json();if(request!==catalogueRequest)return;
  if(!Array.isArray(data))throw new Error('La réponse n’est pas une liste JSON');
  tools=data;$('source').textContent='Données de la base via l’API';$('notice').hidden=true;render();
 }catch(error){
  if(request!==catalogueRequest)return;
  tools=[];$('catalogue').replaceChildren();$('count').textContent='Catalogue indisponible';
  $('source').textContent='Connexion impossible';$('notice').hidden=false;
  $('notice').textContent=`Impossible de charger les outils (${error.message}). Vérifiez que l’API est lancée sur le port 8000, puis réessayez.`;
 }finally{if(request===catalogueRequest){button.disabled=false;button.textContent='↻ Actualiser'}}
}
$('refresh').addEventListener('click',loadTools);
function updateEtatEditor(){
 updateLoanForm();
 const own=currentDetail&&Number($('profile').value)===currentDetail.ownerId;
 $('editEtatForm').hidden=!own;
 if(currentDetail)$('editEtat').value=currentDetail.etat||'';
 $('etatMessage').textContent=own?'':(currentDetail?'Choisissez le profil du propriétaire pour modifier l’état.':'');
}
$('editEtatForm').addEventListener('submit',async(event)=>{
 event.preventDefault();if(!currentDetail)return;
 const id=currentDetail.id;const button=$('saveEtat');button.disabled=true;
 try{
  const response=await fetch(`${API_URL}/api/tools/${id}/etat`,{method:'PATCH',headers:{'Content-Type':'application/json','X-User-Id':$('profile').value},body:JSON.stringify({etat:$('editEtat').value.trim()||null})});
  const data=await response.json();
  if(!response.ok)throw new Error(Array.isArray(data.detail)?data.detail.map(e=>`${e.field} : ${e.message}`).join(' · '):data.detail||'Modification impossible');
  $('details').close();await loadTools();await loadDetail(id);$('etatMessage').textContent='État enregistré.';
 }catch(error){$('etatMessage').textContent=error.message}finally{button.disabled=false}
});
function updateLoanForm(){
 const selected=Number($('profile').value);
 const allowed=currentDetail&&selected&&selected!==currentDetail.ownerId&&currentDetail.status!=='unavailable';
 $('loanForm').hidden=!allowed;
 const today=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Paris'}).format(new Date());
 $('loanStart').min=today;$('loanEnd').min=$('loanStart').value||today;
 $('loanMessage').textContent=!currentDetail?'':(!selected?'Choisissez votre profil pour demander un emprunt.':selected===currentDetail.ownerId?'Vous ne pouvez pas emprunter votre propre outil.':currentDetail.status==='unavailable'?'Cet outil n’est pas disponible.':'');
}
$('loanStart').addEventListener('change',()=>{$('loanEnd').min=$('loanStart').value||$('loanStart').min});
$('loanForm').addEventListener('submit',async(event)=>{
 event.preventDefault();if(!currentDetail)return;
 const button=$('submitLoan');button.disabled=true;
 try{
  const response=await fetch(`${API_URL}/api/tools/${currentDetail.id}/loans`,{method:'POST',headers:{'Content-Type':'application/json','X-User-Id':$('profile').value},body:JSON.stringify({startDate:$('loanStart').value,endDate:$('loanEnd').value})});
  const data=await response.json();
  if(!response.ok)throw new Error(Array.isArray(data.detail)?data.detail.map(e=>`${e.field} : ${e.message}`).join(' · '):data.detail||'Demande impossible');
  $('loanMessage').textContent=`Demande n°${data.id} envoyée : en attente du propriétaire.`;$('loanForm').reset();updateLoanDates();await loadMine();
 }catch(error){$('loanMessage').textContent=error.message}finally{button.disabled=false}
});
function updateLoanDates(){ $('loanEnd').min=$('loanStart').min }
const loanStatusNames={pending:'En attente',accepted:'Acceptée',refused:'Refusée',returned:'Rendue'};
async function loadReceived(){
 const user=$('profile').value;const root=$('receivedLoans');root.replaceChildren();
 if(!user){$('receivedMessage').textContent='Choisissez votre profil.';return}
 $('receivedMessage').textContent='Chargement des demandes…';
 try{
  const response=await fetch(`${API_URL}/api/loans/received`,{headers:{'X-User-Id':user}});
  const data=await response.json();
  if(user!==$('profile').value)return;
  if(!response.ok)throw new Error(Array.isArray(data.detail)?data.detail.map(e=>`${e.field} : ${e.message}`).join(' · '):data.detail||'Chargement impossible');
  $('receivedMessage').textContent=data.length?'':'Aucune demande reçue.';
  for(const loan of data){
   const card=el('article','tool');const body=el('div','details');
   body.append(el('h3','',loan.toolName),el('p','',`${loan.borrower.firstName} — ${loan.borrower.district}`),el('p','',`Du ${loan.startDate} au ${loan.endDate}`),el('p','',loanStatusNames[loan.status]||loan.status));
   const actions=loan.status==='pending'?[['accepted','Accepter'],['refused','Refuser']]:loan.status==='accepted'?[['returned','Déclarer le retour']]:[];
   for(const [status,label] of actions){
    const button=el('button','smallbtn',label);button.type='button';
    button.addEventListener('click',async()=>{
     const buttons=body.querySelectorAll('button');buttons.forEach(b=>b.disabled=true);
     try{
      const result=await fetch(`${API_URL}/api/loans/${loan.id}${status==='returned'?'/return':''}`,{method:'PATCH',headers:{'Content-Type':'application/json','X-User-Id':user},body:status==='returned'?undefined:JSON.stringify({status})});
      const decision=await result.json();
      if(!result.ok)throw new Error(Array.isArray(decision.detail)?decision.detail.map(e=>`${e.field} : ${e.message}`).join(' · '):decision.detail||'Décision impossible');
      await Promise.all([loadReceived(),loadTools(),loadOwned(),loadMine()]);
      if(currentDetail&&currentDetail.id===loan.toolId&&$('details').open){$('details').close();await loadDetail(loan.toolId)}
     }catch(error){$('receivedMessage').textContent=error.message;buttons.forEach(b=>b.disabled=false)}
    });body.append(button);
   }
   if(loan.status==='returned'){
    if(loan.rating!==null&&loan.rating!==undefined)body.append(el('p','',`Note de l’emprunteur : ${loan.rating}/5`));
    else{
     const form=el('form');const label=el('label','',`Note pour ${loan.borrower.firstName} `);const select=el('select');select.required=true;select.setAttribute('aria-label',`Note de l’emprunteur pour le prêt ${loan.id}`);select.append(new Option('Choisir une note',''));for(let i=1;i<=5;i++)select.append(new Option(`${i}/5`,i));label.append(select);const button=el('button','smallbtn','Noter l’emprunteur');button.type='submit';form.append(label,button);
     form.addEventListener('submit',async(event)=>{event.preventDefault();button.disabled=true;try{
      const response=await fetch(`${API_URL}/api/loans/${loan.id}/rating`,{method:'POST',headers:{'Content-Type':'application/json','X-User-Id':user},body:JSON.stringify({score:Number(select.value)})});const data=await response.json();if(!response.ok)throw new Error(Array.isArray(data.detail)?data.detail.map(e=>`${e.field} : ${e.message}`).join(' · '):data.detail||'Notation impossible');await loadReceived();
     }catch(error){$('receivedMessage').textContent=error.message;button.disabled=false}});body.append(form);
    }
   }
   card.append(body);root.append(card);
  }
 }catch(error){if(user===$('profile').value)$('receivedMessage').textContent=error.message}
}
$('refreshReceived').addEventListener('click',loadReceived);
async function loadMine(){
 const user=$('profile').value;const root=$('myLoans');root.replaceChildren();
 if(!user){$('mineMessage').textContent='Choisissez votre profil.';return}
 $('mineMessage').textContent='Chargement…';
 try{
  const response=await fetch(`${API_URL}/api/loans/mine`,{headers:{'X-User-Id':user}});
  const data=await response.json();if(user!==$('profile').value)return;
  if(!response.ok)throw new Error('Impossible de charger mes emprunts');
  $('mineMessage').textContent=data.length?'':'Aucun emprunt pour le moment.';
  for(const loan of data){const card=el('article','tool');const body=el('div','details');body.append(el('h3','',loan.toolName),el('p','',`Du ${loan.startDate} au ${loan.endDate}`),el('p','',loanStatusNames[loan.status]||loan.status));card.append(body);root.append(card)}
 }catch(error){if(user===$('profile').value)$('mineMessage').textContent=error.message}
}
$('refreshMine').addEventListener('click',loadMine);
async function loadOwned(){
 const user=$('profile').value;const root=$('ownedTools');root.replaceChildren();
 if(!user){$('ownedMessage').textContent='Choisissez votre profil.';return}
 $('ownedMessage').textContent='Chargement…';
 try{
  const response=await fetch(`${API_URL}/api/tools/mine`,{headers:{'X-User-Id':user}});
  const data=await response.json();if(user!==$('profile').value)return;
  if(!response.ok)throw new Error('Impossible de charger mes outils');
  $('ownedMessage').textContent=data.length?'':'Vous ne proposez aucun outil.';
  for(const tool of data){const card=el('article','tool');const body=el('div','details');body.append(el('h3','',tool.name),el('p','',statusNames[tool.status]||tool.status),el('p','',`${tool.pendingRequests} demande(s) en attente`));const button=el('button','smallbtn','Ouvrir la fiche');button.type='button';button.addEventListener('click',()=>loadDetail(tool.id));body.append(button);card.append(body);root.append(card)}
 }catch(error){if(user===$('profile').value)$('ownedMessage').textContent=error.message}
}
async function loadUsers(){
 try{
  const response=await fetch(`${API_URL}/api/users`);
  if(!response.ok)throw new Error('Impossible de charger les profils');
  const users=await response.json();
  $('profile').replaceChildren(new Option('Choisir mon profil',''));
  for(const user of users)$('profile').add(new Option(`${user.firstName} — ${user.district}`,user.id));
  $('profile').disabled=false;
 }catch(error){$('saveNotice').textContent=error.message}
}
$('profile').addEventListener('change',()=>{$('openAdd').disabled=!$('profile').value;updateEtatEditor();loadReceived();loadMine();loadOwned()});
$('openAdd').addEventListener('click',()=>{$('addForm').reset();$('addError').textContent='';$('addDialog').showModal()});
$('cancelAdd').addEventListener('click',()=>$('addDialog').close());
$('addForm').addEventListener('submit',async(event)=>{
 event.preventDefault();const button=$('submitAdd');button.disabled=true;$('addError').textContent='';
 try{
  const payload={name:$('toolName').value,category:$('toolCategory').value,description:$('toolDescription').value||null,etat:$('toolEtat').value||null};
  const params=new URLSearchParams();if($('category').value)params.set('category',$('category').value);if($('search').value.trim())params.set('q',$('search').value.trim());
  const response=await fetch(`${API_URL}/api/tools${params.size?'?'+params:''}`,{method:'POST',headers:{'Content-Type':'application/json','X-User-Id':$('profile').value},body:JSON.stringify(payload)});
  const data=await response.json();
  if(!response.ok)throw new Error(Array.isArray(data.detail)?data.detail.map(e=>`${e.field} : ${e.message}`).join(' · '):data.detail||'Ajout impossible');
  $('addDialog').close();$('saveNotice').textContent=`${data.name} a été ajouté et est disponible.`;
  $('search').value='';$('category').value='';await Promise.all([loadTools(),loadOwned()]);
 }catch(error){$('addError').textContent=error.message}finally{button.disabled=false}
});
for(const category of Object.keys(iconByCat))$('toolCategory').add(new Option(category,category));
fillCategories();loadTools();loadUsers();

