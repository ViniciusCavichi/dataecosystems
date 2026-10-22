const $=s=>document.querySelector(s);
let data={clients:[],appointments:[],records:[]},page='dashboard',search='',selectedClient='';
const titles={dashboard:'Visão geral',agenda:'Agenda',clients:'Clientes',records:'Prontuários'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const localDate=()=>{let d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`};
let agendaDate=localDate();
const date=s=>new Date(s.length===10?s+'T12:00':s).toLocaleDateString('pt-BR',{day:'2-digit',month:'short',year:'numeric'});
const client=id=>data.clients.find(c=>c.id===Number(id));
const initials=n=>n.split(' ').filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase();
const badge=s=>`<span class="badge ${s==='Concluído'?'done':s==='Cancelado'?'cancelled':''}">${esc(s)}</span>`;
function empty(title,detail,action=''){return `<div class="empty"><span>✧</span><h3>${title}</h3><p>${detail}</p>${action}</div>`}
function head(eyebrow,title,desc,button){return `<div class="page-heading"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${desc}</p></div>${button||''}</div>`}
const addButton=(kind,label)=>`<button class="primary" data-add="${kind}">＋ ${label}</button>`;
async function api(path,method='GET',body){const r=await fetch('/api/'+path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const d=await r.json();if(!r.ok)throw Error(d.error||'Não foi possível salvar.');return d}
async function load(){try{data=await api('data');render()}catch(e){$('#content').innerHTML=empty('Não foi possível carregar os dados',esc(e.message),'<button class="secondary" onclick="location.reload()">Tentar novamente</button>')}}
function appointmentRows(items){return items.map(a=>`<div class="appointment"><div class="time">${esc(a.starts_at.slice(11))}<small>${a.duration} min</small></div><div class="avatar">${esc(initials(client(a.client_id)?.name||'?'))}</div><div class="appointment-info"><strong>${esc(client(a.client_id)?.name)}</strong><small>${esc(a.service)}</small></div>${badge(a.status)}<button class="text-button" data-edit="appointments:${a.id}">Editar</button></div>`).join('')}
function render(){
 $('#breadcrumb').textContent=titles[page];document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===page));
 const todayAppointments=data.appointments.filter(a=>a.starts_at.startsWith(localDate())).sort((a,b)=>a.starts_at.localeCompare(b.starts_at));
 const allSorted=[...data.appointments].sort((a,b)=>a.starts_at.localeCompare(b.starts_at));
 let html='';
 if(page==='dashboard'){
 const active=todayAppointments.filter(a=>a.status!=='Cancelado');
 html=head('BEM-VINDA AO SEU ESPAÇO','Cuidar começa com organização.','Uma visão tranquila do seu dia e de quem você cuida.',addButton('appointments','Novo agendamento'));
 html+=`<div class="stats"><div class="stat"><span>Atendimentos hoje <i>▦</i></span><strong>${active.length}</strong><small>Seu dia, com tudo em ordem</small></div><div class="stat"><span>Clientes cadastrados <i>♧</i></span><strong>${data.clients.length}</strong><small>Cada pessoa, uma história</small></div><div class="stat"><span>Atendimentos concluídos <i>✓</i></span><strong>${data.appointments.filter(a=>a.status==='Concluído').length}</strong><small>Cuidado que se transforma</small></div></div>`;
 html+=`<div class="dashboard-grid"><section class="panel"><div class="panel-heading"><div><h2>Agenda de hoje</h2><p>${date(localDate())}</p></div><button class="text-button" data-goto="agenda">Ver agenda ↗</button></div>${todayAppointments.length?appointmentRows(todayAppointments):empty('Um dia cheio de possibilidades','Seus agendamentos de hoje aparecerão aqui.',addButton('appointments','Agendar atendimento'))}</section><section class="care-card"><div class="flower">✳</div><div class="eyebrow">CUIDADO EM CADA ETAPA</div><h2>Pequenos detalhes.<br>Grandes evoluções.</h2><p>Registre cada atendimento e acompanhe a jornada de cuidado de seus pacientes.</p><button class="secondary" data-goto="records">Acessar prontuários ↗</button></section></div>`;
 html+=`<section class="panel recent"><div class="panel-heading"><div><h2>Clientes recentes</h2><p>Conexões que merecem atenção</p></div><button class="text-button" data-goto="clients">Ver todos ↗</button></div>${data.clients.length?`<div class="client-strip">${data.clients.slice(0,4).map(c=>`<button class="mini-client" data-profile="${c.id}"><span class="avatar">${esc(initials(c.name))}</span><strong>${esc(c.name)}</strong><small>${esc(c.phone||'Telefone não informado')}</small></button>`).join('')}</div>`:empty('Sua história começa aqui','Cadastre seu primeiro cliente para começar.',addButton('clients','Cadastrar cliente'))}</section>`;
 }
 if(page==='agenda'){
 html=head('TEMPO PARA CUIDAR','Sua agenda','Organize seus horários e acompanhe cada atendimento.',addButton('appointments','Novo agendamento'));
 let items=allSorted.filter(a=>a.starts_at.startsWith(agendaDate));
 html+=`<section class="panel"><div class="toolbar"><label>Data do atendimento <input type="date" id="agenda-date" value="${agendaDate}"></label><span>${items.length} agendamento(s)</span></div>${items.length?appointmentRows(items):empty('Nenhum atendimento nesta data','Escolha outra data ou reserve um novo horário.')}</section>`;
 }
 if(page==='clients'){
 html=head('PESSOAS E HISTÓRIAS','Seus clientes','Todas as informações para um cuidado mais próximo.',addButton('clients','Novo cliente'));
 let items=data.clients.filter(c=>[c.name,c.phone,c.email,c.instagram].join(' ').toLowerCase().includes(search.toLowerCase()));
 html+=`<section class="panel"><div class="toolbar"><input class="search" id="search" placeholder="Buscar por nome, telefone, e-mail ou Instagram" value="${esc(search)}"><span>${items.length} cliente(s)</span></div>${items.length?`<div class="table-wrap"><table><thead><tr><th>CLIENTE</th><th>CONTATO</th><th>INSTAGRAM</th><th></th></tr></thead><tbody>${items.map(c=>`<tr><td><div class="person"><span class="avatar">${esc(initials(c.name))}</span><div><strong>${esc(c.name)}</strong><small>${c.age===null?'Idade não informada':c.age+' anos'}</small></div></div></td><td>${esc(c.phone||'—')}<small>${esc(c.email)}</small></td><td>${esc(c.instagram||'—')}</td><td><button class="text-button" data-profile="${c.id}">Prontuário ↗</button><button class="text-button" data-edit="clients:${c.id}">Editar</button></td></tr>`).join('')}</tbody></table></div>`:empty('Nenhum cliente encontrado','Cadastre um cliente ou ajuste sua busca.')}</section>`;
 }
 if(page==='records'){
 html=head('ACOMPANHAMENTO INDIVIDUAL','Prontuários','Cada evolução faz parte de uma história de cuidado.',selectedClient?addButton('records','Registrar evolução'):'');
 html+=`<section class="panel"><div class="toolbar"><label class="patient-select">Selecione um paciente<select id="patient"><option value="">Escolha um cliente</option>${data.clients.map(c=>`<option value="${c.id}" ${String(c.id)===String(selectedClient)?'selected':''}>${esc(c.name)}</option>`).join('')}</select></label></div>`;
 let c=client(selectedClient);
 if(!c)html+=empty('Um olhar atento a cada evolução','Selecione um paciente para consultar seu histórico.');
 else{
 let records=data.records.filter(r=>r.client_id===c.id).sort((a,b)=>b.date.localeCompare(a.date)||b.id-a.id);
 html+=`<div class="profile"><div class="person"><span class="avatar large">${esc(initials(c.name))}</span><div><h2>${esc(c.name)}</h2><p>${c.age===null?'Idade não informada':c.age+' anos'} · ${esc(c.phone||'Telefone não informado')}</p></div></div><dl><div><dt>E-mail</dt><dd>${esc(c.email||'—')}</dd></div><div><dt>Endereço</dt><dd>${esc(c.address||'—')}</dd></div><div><dt>Instagram</dt><dd>${esc(c.instagram||'—')}</dd></div></dl>${c.notes?`<div class="note"><strong>Observações do cadastro</strong><p>${esc(c.notes)}</p></div>`:''}</div><div class="history-title"><h2>Linha do tempo de cuidados</h2><span>${records.length} registro(s)</span></div>`;
 html+=records.length?`<div class="timeline">${records.map(r=>`<article class="record"><div class="record-heading"><div><span class="eyebrow">${date(r.date)}</span><h3>${esc(r.procedure)}</h3></div><div><button class="text-button" data-edit="records:${r.id}">Editar</button><button class="text-button danger" data-delete="records:${r.id}">Excluir</button></div></div><label>Evolução do atendimento</label><p>${esc(r.evolution)}</p>${r.recommendations?`<label>Orientações e próximos passos</label><p>${esc(r.recommendations)}</p>`:''}</article>`).join('')}</div>`:empty('O primeiro capítulo do cuidado','Registre procedimentos, evolução e orientações deste paciente.');
 }
 html+='</section>';
 }
 $('#content').innerHTML=html;
}
const input=(name,label,type='text',value='',required=false)=>`<label>${label}${required?' *':''}<input name="${name}" type="${type}" value="${esc(value)}" ${required?'required':''} ${name==='age'?'min="0" max="120"':''}></label>`;
const area=(name,label,value='',required=false)=>`<label class="full">${label}${required?' *':''}<textarea name="${name}" rows="3" ${required?'required':''}>${esc(value)}</textarea></label>`;
let editing=null;
function openForm(table,id){
 if(table!=='clients'&&!data.clients.length){toast('Cadastre um cliente antes de registrar atendimentos.');page='clients';render();openForm('clients');return}
 const d=id?data[table].find(x=>x.id===Number(id)):{};editing={table,id};
 $('#modal-title').textContent=(id?'Editar ':'Novo ')+({clients:'cliente',appointments:'agendamento',records:'registro de evolução'}[table]);
 const options=(name,label,values,value)=>`<label>${label} *<select name="${name}" required>${values.map(([v,t])=>`<option value="${esc(v)}" ${String(v)===String(value)?'selected':''}>${esc(t)}</option>`).join('')}</select></label>`;
 let fields='';
 if(table==='clients')fields=input('name','Nome completo','text',d.name,true)+input('age','Idade','number',d.age)+input('phone','Telefone','tel',d.phone)+input('email','E-mail','email',d.email)+input('instagram','Instagram','text',d.instagram)+input('address','Endereço','text',d.address)+area('notes','Observações',d.notes);
 if(table==='appointments')fields=options('client_id','Cliente',data.clients.map(c=>[c.id,c.name]),d.client_id)+input('starts_at','Data e horário','datetime-local',d.starts_at||agendaDate+'T09:00',true)+input('service','Procedimento','text',d.service,true)+input('duration','Duração em minutos','number',d.duration||60,true)+options('status','Status',['Agendado','Confirmado','Concluído','Cancelado'].map(x=>[x,x]),d.status||'Agendado')+area('notes','Observações do agendamento',d.notes);
 if(table==='records')fields=options('client_id','Paciente',data.clients.map(c=>[c.id,c.name]),d.client_id||selectedClient)+input('date','Data do atendimento','date',d.date||localDate(),true)+input('procedure','Procedimento realizado','text',d.procedure,true)+area('evolution','Evolução do atendimento',d.evolution,true)+area('recommendations','Orientações e próximos passos',d.recommendations);
 $('#fields').innerHTML=fields;$('#form-error').textContent='';$('#modal').showModal();
}
function toast(msg){$('#toast').textContent=msg;$('#toast').classList.add('visible');setTimeout(()=>$('#toast').classList.remove('visible'),3500)}
document.addEventListener('click',async e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.page||b.dataset.goto){page=b.dataset.page||b.dataset.goto;search='';render()}
 if(b.dataset.add)openForm(b.dataset.add);
 if(b.dataset.edit){const[t,id]=b.dataset.edit.split(':');openForm(t,id)}
 if(b.dataset.profile){selectedClient=b.dataset.profile;page='records';render()}
 if(b.dataset.delete&&confirm('Excluir este registro de evolução? Esta ação não pode ser desfeita.')){const[t,id]=b.dataset.delete.split(':');try{await api(t+'/'+id,'DELETE');await load();toast('Registro excluído.')}catch(e){toast(e.message)}}
});
document.addEventListener('change',e=>{if(e.target.id==='agenda-date'){agendaDate=e.target.value;render()}if(e.target.id==='patient'){selectedClient=e.target.value;render()}});
document.addEventListener('input',e=>{if(e.target.id==='search'){const pos=e.target.selectionStart;search=e.target.value;render();$('#search').focus();$('#search').setSelectionRange(pos,pos)}});
$('#close-modal').onclick=$('#cancel').onclick=()=>$('#modal').close();
$('#form').onsubmit=async e=>{e.preventDefault();const button=$('#form button[type=submit]');button.disabled=true;try{const values=Object.fromEntries(new FormData(e.target));await api(editing.table+(editing.id?'/'+editing.id:''),editing.id?'PUT':'POST',values);if(editing.table==='records')selectedClient=values.client_id;$('#modal').close();await load();toast('Informações salvas com sucesso.')}catch(e){$('#form-error').textContent=e.message}finally{button.disabled=false}};
$('#today').textContent=new Date().toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'});
load();
