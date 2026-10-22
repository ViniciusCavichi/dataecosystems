const $=s=>document.querySelector(s),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const now=()=>{let d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`},br=d=>d?d.split('-').reverse().join('/'):'—',money=n=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(n/100);
let data={clients:[],vehicles:[],tasks:[],quotes:[],settings:{}},page='dashboard',query='',day=now(),view='day',editing=null,logo='',draftItems=[];
const names={dashboard:'Visão geral',tasks:'Planejador',clients:'Clientes',vehicles:'Veículos',quotes:'Orçamentos',settings:'Dados da oficina'},cn=id=>data.clients.find(c=>c.id===Number(id))?.name||'Sem cliente',vn=id=>data.vehicles.find(v=>v.id===Number(id))?.name||'Sem veículo';
async function api(path,method='GET',body){let r=await fetch('/api/'+path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});let d=await r.json();if(!r.ok)throw Error(d.error||'Falha na operação.');return d}
function toast(s){$('#toast').textContent=s;$('#toast').classList.add('visible');setTimeout(()=>$('#toast').classList.remove('visible'),4000)}
async function load(){data=await api('data');logo=data.settings.logo||'';$('#welcome-logo').src=$('#nav-logo').src=logo||'/logo.svg';render()}
const add=(t,s)=>`<button class="primary" data-add="${t}">＋ ${s}</button>`,badge=s=>`<span class="badge ${s==='Concluída'||s==='Aprovado'?'green':s==='Alta'||s==='Entrega'?'red':''}">${esc(s)}</span>`,empty=s=>`<div class="empty"><span>＋</span><h3>${s}</h3><p>Organize sua oficina, um registro por vez.</p></div>`;
function heading(title,desc,action=''){return `<div class="heading"><div><div class="eyebrow">CONTROLE DA OPERAÇÃO</div><h1>${title}</h1><p>${desc}</p></div>${action}</div>`}
function buttons(t,id){return `<button class="text" data-edit="${t}:${id}">Editar</button><button class="text danger" data-delete="${t}:${id}">Excluir</button>`}
const quoteTotal=q=>q.items.reduce((a,i)=>a+i.total_cents,0);
function taskCard(t){return `<article class="task"><div class="task-top"><span>${esc(t.time||'Sem horário')} · ${br(t.date)}</span>${badge(t.priority)}</div><h3>${esc(t.title)}</h3><p>${esc(t.client_id?cn(t.client_id):'Tarefa interna')}${t.vehicle_id?' · '+esc(vn(t.vehicle_id)):''}</p>${t.notes?`<p class="pre">${esc(t.notes)}</p>`:''}<div class="task-bottom">${badge(t.status)}<div>${t.status!=='Concluída'&&t.status!=='Cancelada'?`<button class="text" data-done="${t.id}">✓ Concluir</button>`:''}${buttons('tasks',t.id)}</div></div></article>`}
function table(headers,rows){return `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`}
function render(){
 $('#crumb').textContent=names[page];document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===page));let h='';
 if(page==='dashboard'){
 let pending=data.tasks.filter(t=>!['Concluída','Cancelada'].includes(t.status));
 h=heading('Sua oficina. Sob controle.','Da primeira ideia à entrega do triciclo.',add('tasks','Nova tarefa'));
 h+=`<div class="stats"><div><span>TAREFAS HOJE</span><strong>${pending.filter(t=>t.date===now()).length}</strong><small>Planejamento do dia</small></div><div><span>ENTREGAS PENDENTES</span><strong>${pending.filter(t=>t.priority==='Entrega').length}</strong><small>Compromissos com seus clientes</small></div><div><span>ORÇAMENTOS EM ABERTO</span><strong>${data.quotes.filter(q=>['Rascunho','Enviado'].includes(q.status)).length}</strong><small>Oportunidades na garagem</small></div><div><span>VEÍCULOS CADASTRADOS</span><strong>${data.vehicles.length}</strong><small>${data.clients.length} clientes na base</small></div></div>`;
 h+=`<div class="dashboard-grid"><section class="panel"><div class="panel-title"><h2>Na bancada hoje</h2><button class="text" data-goto="tasks">Abrir planejador ↗</button></div>${pending.filter(t=>t.date<=now()).length?pending.filter(t=>t.date<=now()).sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time)).map(taskCard).join(''):empty('A bancada está livre')}</section><section class="feature"><span class="eyebrow">RCP GARAGE</span><h2>Feito para rodar.<br>Planejado para entregar.</h2><p>Transforme serviços e peças em um orçamento claro para seu cliente.</p>${add('quotes','Criar orçamento')}<div class="feature-mark">RCP</div></section></div>`;
 }
 if(page==='tasks'){
 h=heading('Planejador da oficina','Rotina diária, fabricação, manutenção e prazos de entrega.',add('tasks','Nova tarefa'));
 h+=`<section class="panel"><div class="toolbar"><label>Data de referência<input type="date" id="day" value="${day}"></label><div class="segments"><button class="${view==='day'?'selected':''}" data-view="day">Dia</button><button class="${view==='week'?'selected':''}" data-view="week">7 dias</button><button class="${view==='all'?'selected':''}" data-view="all">Todas</button></div></div>`;
 let end=new Date(day+'T12:00:00');end.setDate(end.getDate()+6);let endDate=`${end.getFullYear()}-${String(end.getMonth()+1).padStart(2,'0')}-${String(end.getDate()).padStart(2,'0')}`;
 let tasks=data.tasks.filter(t=>view==='all'||(view==='day'?t.date===day:t.date>=day&&t.date<=endDate)).sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time));
 h+=`<div class="kanban">${['A fazer','Em andamento','Concluída','Cancelada'].map(s=>`<section><div class="column-title">${s} <b>${tasks.filter(t=>t.status===s).length}</b></div>${tasks.filter(t=>t.status===s).map(taskCard).join('')||'<p class="column-empty">Nenhuma tarefa</p>'}</section>`).join('')}</div></section>`;
 }
 if(page==='clients'||page==='vehicles'){
 let is=page==='clients',rows=data[page].filter(r=>Object.values(r).join(' ').toLowerCase().includes(query.toLowerCase()));
 h=heading(is?'Clientes':'Veículos',is?'Relacionamentos que movem a garagem.':'Cada triciclo com seu proprietário e sua história.',add(page,is?'Novo cliente':'Novo veículo'));
 h+=`<section class="panel"><div class="toolbar"><input id="search" placeholder="Buscar ${is?'cliente':'veículo'}…" value="${esc(query)}"><span>${rows.length} registro(s)</span></div>`;
 h+=rows.length?table(is?['CLIENTE','CONTATO','ENDEREÇO','AÇÕES']:['VEÍCULO','PROPRIETÁRIO','IDENTIFICAÇÃO','AÇÕES'],rows.map(r=>is?`<tr><td><strong>${esc(r.name)}</strong><small>${r.age==null?'Idade não informada':r.age+' anos'}</small></td><td>${esc(r.phone||'—')}<small>${esc(r.email)} ${esc(r.instagram)}</small></td><td>${esc(r.address||'—')}</td><td>${buttons(page,r.id)}</td></tr>`:`<tr><td><strong>${esc(r.name)}</strong><small>${esc(r.color)} ${esc(r.year)}</small></td><td>${esc(cn(r.client_id))}</td><td>${esc(r.plate||'Sem placa')}<small>Chassi: ${esc(r.chassis||'—')}</small></td><td>${buttons(page,r.id)}</td></tr>`)):empty(is?'Cadastre seu primeiro cliente':'Cadastre o primeiro veículo');h+='</section>';
 }
 if(page==='quotes'){
 h=heading('Orçamentos','Serviços, peças e valores apresentados com clareza.',add('quotes','Novo orçamento'));
 h+='<section class="panel">'+(data.quotes.length?table(['NÚMERO / EMISSÃO','CLIENTE / VEÍCULO','STATUS','TOTAL','AÇÕES'],data.quotes.map(q=>`<tr><td><strong>#${String(q.id).padStart(5,'0')}</strong><small>${br(q.date)}</small></td><td>${esc(cn(q.client_id))}<small>${esc(q.vehicle_id?vn(q.vehicle_id):'Sem veículo')}</small></td><td>${badge(q.status)}</td><td><strong>${money(quoteTotal(q))}</strong></td><td><a class="pdf" href="/api/pdf/${q.id}" download>↓ PDF</a>${buttons('quotes',q.id)}</td></tr>`)):empty('Seu próximo projeto começa com um orçamento'))+'</section>';
 }
 if(page==='settings'){
 let s=data.settings;h=heading('Dados da oficina','Estas informações identificam a RCP Garage nos PDFs.');
 h+=`<section class="panel settings"><form id="settings-form"><div class="fields">${input('name','Nome da oficina',s.name,'text',true)}${input('document','CNPJ / CPF',s.document)}${input('phone','Telefone',s.phone,'tel')}${input('email','E-mail',s.email,'email')}${input('address','Endereço',s.address)}<label>Logo da oficina<input id="logo-file" type="file" accept="image/png,image/jpeg,image/webp"><small>PNG, JPEG ou WebP, até 2 MB. Aparece na entrada e no menu.</small></label></div><div class="logo-preview"><img src="${esc(logo||'/logo.svg')}" alt="Logo atual"><p>Selecione aqui a imagem original da RCP Garage que você enviou na conversa.</p></div><p class="muted">O PDF utiliza o nome e os dados da oficina em texto, com cabeçalho vermelho.</p><button class="primary" type="submit">Salvar dados da oficina</button></form></section>`;
 }
 $('#content').innerHTML=h;
}
function input(n,l,v='',type='text',required=false){return `<label>${l}${required?' *':''}<input name="${n}" type="${type}" value="${esc(v)}" ${required?'required':''} ${n==='age'?'min="0" max="120"':''}></label>`}
function area(n,l,v=''){return `<label class="full">${l}<textarea name="${n}" rows="3">${esc(v)}</textarea></label>`}
function select(n,l,opts,val='',required=false){return `<label>${l}${required?' *':''}<select name="${n}" ${required?'required':''}>${opts.map(([id,title])=>`<option value="${esc(id)}" ${String(id)===String(val)?'selected':''}>${esc(title)}</option>`).join('')}</select></label>`}
function vehicleOptions(cid){return [['','Sem veículo vinculado'],...data.vehicles.filter(v=>String(v.client_id)===String(cid)).map(v=>[v.id,v.name+(v.plate?' · '+v.plate:'')])]}
function renderItems(){
 $('#items').innerHTML=draftItems.map((i,n)=>`<div class="item-row"><label>Serviço / peça *<input data-item="${n}:description" value="${esc(i.description)}" required></label><label>Qtd. *<input data-item="${n}:quantity" type="number" min="0.001" step="0.001" value="${esc(i.quantity)}" required></label><label>Unitário (R$) *<input data-item="${n}:price" type="number" min="0" max="100000000" step="0.01" value="${esc(i.price)}" required></label><strong class="item-total">${money(Math.round(Number(i.quantity||0)*Math.round(Number(i.price||0)*100)))}</strong><button class="text danger" type="button" data-remove-item="${n}" aria-label="Remover item">×</button></div>`).join('');updateTotal();
}
function updateTotal(){let total=0;draftItems.forEach((i,n)=>{let value=Math.round(Number(i.quantity||0)*Math.round(Number(i.price||0)*100));total+=value;document.querySelectorAll('.item-total')[n].textContent=money(value)});$('#quote-total').textContent=money(total)}
function openForm(t,id){
 if(['vehicles','quotes'].includes(t)&&!data.clients.length){toast('Cadastre um cliente primeiro.');page='clients';render();return}
 let d=id?data[t].find(r=>r.id===Number(id)):{};editing={table:t,id};$('#modal-title').textContent=(id?'Editar ':'Novo ')+({clients:'cliente',vehicles:'veículo',tasks:'tarefa',quotes:'orçamento'}[t]);let f='';
 let cid=d.client_id||(t==='vehicles'||t==='quotes'?data.clients[0]?.id:'');
 const clientsSelect=select('client_id','Cliente',[['','Tarefa interna / sem cliente'],...data.clients.map(c=>[c.id,c.name])],cid,t==='vehicles'||t==='quotes');
 if(t==='clients')f=input('name','Nome completo',d.name,'text',true)+input('age','Idade',d.age,'number')+input('phone','Telefone',d.phone,'tel')+input('email','E-mail',d.email,'email')+input('instagram','Instagram',d.instagram)+input('address','Endereço',d.address)+area('notes','Observações',d.notes);
 if(t==='vehicles')f=clientsSelect+input('name','Modelo / identificação',d.name,'text',true)+input('plate','Placa',d.plate)+input('year','Ano',d.year,'number')+input('chassis','Chassi',d.chassis)+input('color','Cor',d.color)+area('notes','Observações e características',d.notes);
 if(t==='tasks')f=input('title','Tarefa / entrega',d.title,'text',true)+input('date','Data planejada',d.date||day,'date',true)+input('time','Horário (opcional)',d.time,'time')+select('priority','Prioridade',['Normal','Alta','Entrega'].map(x=>[x,x]),d.priority||'Normal',true)+select('status','Etapa',['A fazer','Em andamento','Concluída','Cancelada'].map(x=>[x,x]),d.status||'A fazer',true)+clientsSelect+select('vehicle_id','Veículo',vehicleOptions(cid),d.vehicle_id)+area('notes','Descrição / checklist da rotina',d.notes);
 if(t==='quotes'){
 f=clientsSelect+select('vehicle_id','Veículo',vehicleOptions(cid),d.vehicle_id)+input('date','Data de emissão',d.date||now(),'date',true)+input('valid_until','Válido até',d.valid_until,'date')+select('status','Situação',['Rascunho','Enviado','Aprovado','Recusado'].map(x=>[x,x]),d.status||'Rascunho',true)+`<section class="full quote-items"><h3>Serviços e peças</h3><div id="items"></div><button type="button" class="secondary" id="add-item">＋ Adicionar item</button><div class="quote-total">TOTAL <strong id="quote-total"></strong></div></section>`+area('notes','Condições de pagamento, prazo de entrega e observações',d.notes);
 draftItems=d.items?d.items.map(i=>({description:i.description,quantity:i.quantity,price:(i.price_cents/100).toFixed(2)})):[{description:'',quantity:'1',price:'0.00'}];
 }
 $('#fields').innerHTML=f;$('#error').textContent='';if(t==='quotes')renderItems();$('#modal').showModal();
}
document.addEventListener('click',async e=>{let b=e.target.closest('button');if(!b)return;
 if(b.dataset.page||b.dataset.goto){page=b.dataset.page||b.dataset.goto;query='';render()}
 if(b.dataset.add)openForm(b.dataset.add);
 if(b.dataset.edit){let[t,id]=b.dataset.edit.split(':');openForm(t,id)}
 if(b.dataset.delete&&confirm('Excluir este registro? Esta ação não pode ser desfeita.')){let[t,id]=b.dataset.delete.split(':');try{await api(t+'/'+id,'DELETE');await load();toast('Registro excluído.')}catch(e){toast(e.message)}}
 if(b.dataset.done){let t=data.tasks.find(t=>t.id===Number(b.dataset.done));try{await api('tasks/'+t.id,'PUT',{...t,status:'Concluída'});await load();toast('Tarefa concluída.')}catch(e){toast(e.message)}}
 if(b.dataset.view){view=b.dataset.view;render()}
 if(b.id==='add-item'){draftItems.push({description:'',quantity:'1',price:'0.00'});renderItems()}
 if(b.dataset.removeItem!==undefined){if(draftItems.length===1){toast('O orçamento precisa de pelo menos um item.');return}draftItems.splice(Number(b.dataset.removeItem),1);renderItems()}
});
document.addEventListener('input',e=>{
 if(e.target.id==='search'){let pos=e.target.selectionStart;query=e.target.value;render();$('#search').focus();$('#search').setSelectionRange(pos,pos)}
 if(e.target.dataset.item){let[n,key]=e.target.dataset.item.split(':');draftItems[n][key]=e.target.value;updateTotal()}
});
document.addEventListener('change',async e=>{
 if(e.target.id==='day'){if(e.target.value){day=e.target.value;render()}}
 if(e.target.name==='client_id'&&$('#form [name=vehicle_id]')){let sel=$('#form [name=vehicle_id]');sel.innerHTML=vehicleOptions(e.target.value).map(([id,n])=>`<option value="${id}">${esc(n)}</option>`).join('')}
 if(e.target.id==='logo-file'){
  let f=e.target.files[0];if(!f)return;if(f.size>2*1024*1024){toast('A logo deve ter até 2 MB.');return}
  let reader=new FileReader();reader.onload=()=>{logo=reader.result;$('.logo-preview img').src=logo};reader.readAsDataURL(f);
 }
});
document.addEventListener('submit',async e=>{
 if(e.target.id!=='settings-form')return;e.preventDefault();let button=e.target.querySelector('button[type=submit]');button.disabled=true;
 try{await api('settings','PUT',{...Object.fromEntries(new FormData(e.target)),logo});await load();toast('Dados da oficina salvos.')}catch(err){toast(err.message)}finally{button.disabled=false}
});
$('#form').onsubmit=async e=>{e.preventDefault();let button=$('#form button[type=submit]');button.disabled=true;try{let d=Object.fromEntries(new FormData(e.target));if(editing.table==='quotes')d.items=draftItems;await api(editing.table+(editing.id?'/'+editing.id:''),editing.id?'PUT':'POST',d);$('#modal').close();await load();toast('Salvo com sucesso.')}catch(err){$('#error').textContent=err.message}finally{button.disabled=false}};
$('#close').onclick=$('#cancel').onclick=()=>$('#modal').close();
$('#access').onclick=()=>{$('#welcome').hidden=true;$('#workspace').hidden=false};
$('#exit').onclick=()=>{$('#workspace').hidden=true;$('#welcome').hidden=false};
$('#today').textContent=new Date().toLocaleDateString('pt-BR',{day:'numeric',month:'long',year:'numeric'});
load().catch(e=>{$('#access').disabled=true;toast('Não foi possível conectar: '+e.message)});
