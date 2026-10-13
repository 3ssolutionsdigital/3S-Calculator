// Save a qualified contact lead before the visitor enters bill or roof details.
t.en.leadFirstTitle='First, how can we reach you?';
t.en.leadFirstHint='Share your details to continue. Your request is saved before the estimate starts.';
t.en.continueEstimate='Save details & continue';
t.te.leadFirstTitle='ముందుగా, మిమ్మల్ని ఎలా సంప్రదించాలి?';
t.te.leadFirstHint='కొనసాగించడానికి మీ వివరాలు ఇవ్వండి. అంచనా ప్రారంభానికి ముందే మీ అభ్యర్థన సేవ్ అవుతుంది.';
t.te.continueEstimate='వివరాలు సేవ్ చేసి కొనసాగించండి';
var leadId=null, leadDetails=null;

function goCalc(c){category=c||'residential';step=0;calc=null;leadId=null;leadDetails=null;page='wizard';render();window.scrollTo(0,0)}
function showSection(id){page='landing';history.replaceState(null,'','#'+id);render();requestAnimationFrame(()=>document.getElementById(id)?.scrollIntoView({behavior:'smooth'}))}
function header(){return `<header class="topbar"><a href="#home" onclick="showSection('home');return false" aria-label="3S Solutions home"><img class="logo" src="assets/3s-solutions-logo.png" alt="3S Solutions"></a><nav class="nav"><a href="#calculator" onclick="showSection('calculator');return false">${tr('navCalc')}</a><a href="#how" onclick="showSection('how');return false">${tr('navHow')}</a><a href="#about" onclick="showSection('about');return false">${tr('navAbout')}</a><button class="lang" onclick="changeLang()">${lang==='en'?'తెలుగు':'English'}</button></nav></header>`}
function changeLang(){const ids=step===1?['leadName','leadPhone','leadEmail','leadCity','businessName','leadConsent','leadMarketing','leadState']:step===2?['state','city','bill','roof','units','hours','shade','property']:[];const state={};ids.forEach(id=>{const el=document.getElementById(id);if(el)state[id]=el.type==='checkbox'?el.checked:el.value});lang=lang==='en'?'te':'en';try{localStorage.setItem('3s-lang',lang)}catch{}render();Object.entries(state).forEach(([id,value])=>{const el=document.getElementById(id);if(el){if(el.type==='checkbox')el.checked=value;else el.value=value}})}

function wizard(){
  const labels=[tr('home'),tr('business'),tr('industry')],cats=['residential','commercial','industrial'];
  let body='';
  if(step===0) body=`<div class="panel"><h2>${tr('typesTitle')}</h2><p>${tr('typesSub')}</p><div class="customer-types">${cats.map((c,i)=>`<button class="type ${c===category?'active':''}" onclick="category='${c}';render()"><b>${labels[i]}</b><small>${tr(['homeDesc','businessDesc','industryDesc'][i])}</small></button>`).join('')}</div><div class="panel-actions"><button class="btn secondary" onclick="renderLanding()">${tr('back')}</button><button class="btn" onclick="step=1;render()">${tr('next')} →</button></div></div>`;
  else if(step===1) body=`<div class="panel"><h2>${tr('leadFirstTitle')}</h2><p>${tr('leadFirstHint')}</p><div class="fields"><div class="field"><label>${tr('name')} *</label><input id="leadName" autocomplete="name"></div><div class="field"><label>${tr('phone')} *</label><input id="leadPhone" type="tel" autocomplete="tel" placeholder="+91"></div><div class="field"><label>${tr('email')}</label><input id="leadEmail" type="email" autocomplete="email"></div><div class="field"><label>${tr('state')} *</label><select id="leadState"><option>Andhra Pradesh</option><option>Telangana</option><option>Other</option></select></div><div class="field"><label>${tr('city')} *</label><input id="leadCity" autocomplete="address-level2" placeholder="e.g. Vijayawada"></div>${category!=='residential'?`<div class="field"><label>${tr('business')}</label><input id="businessName" autocomplete="organization"></div>`:''}</div><label class="check"><input id="leadConsent" type="checkbox"> ${tr('consent')}</label><label class="check"><input id="leadMarketing" type="checkbox"> ${tr('marketing')}</label><div class="panel-actions"><button class="btn secondary" onclick="step=0;render()">${tr('back')}</button><button class="btn" onclick="saveLeadFirst()">${tr('continueEstimate')} →</button></div></div>`;
  else if(step===2) body=`<div class="panel"><h2>${tr('basics')}</h2><p>${tr('basicsd')}</p><div class="status">${tr('saved')}</div><div class="fields"><div class="field"><label>${tr('state')}</label><select id="state"><option ${leadDetails.state==='Andhra Pradesh'?'selected':''}>Andhra Pradesh</option><option ${leadDetails.state==='Telangana'?'selected':''}>Telangana</option><option ${leadDetails.state==='Other'?'selected':''}>Other</option></select></div><div class="field"><label>${tr('city')}</label><input id="city" value="${escapeHtml(leadDetails.city)}"></div><div class="field"><label>${tr('bill')} (₹)</label><input id="bill" type="number" min="100" placeholder="e.g. 8,000"></div><div class="field"><label>${tr('roof')}</label><input id="roof" type="number" min="0" placeholder="e.g. 100"><div class="hint">${tr('roofhint')}</div></div><div class="field"><label>${tr('shade')}</label><select id="shade"><option value="unknown">${tr('unknown')}</option><option value="sunny">${tr('sunny')}</option><option value="some">${tr('some')}</option><option value="heavy">${tr('heavy')}</option></select></div><div class="field"><label>${tr('property')}</label><select id="property"><option>${tr('homeType')}</option><option>${tr('apt')}</option><option>${tr('other')}</option></select></div><div class="field"><label>${tr('units')}</label><input id="units" type="number" min="1" placeholder="e.g. 950"></div>${category!=='residential'?`<div class="field"><label>${tr('operating')}</label><input id="hours" type="number" min="1" max="24" value="10"></div>`:''}</div><div class="panel-actions"><span></span><button class="btn" onclick="makeCalc()">${tr('calc')} →</button></div></div>`;
  else body=calc?results():`<div class="panel loading">${tr('apiError')}</div>`;
  return `${header()}<main class="shell"><div class="wizard"><div class="crumb"><a href="#home" onclick="renderLanding();return false">${tr('landing')}</a>　/　${tr(category)}　 ·　${tr('step')} ${step+1} ${tr('of')} 4</div><div class="progress"><i style="width:${(step+1)*25}%"></i></div>${body}<p class="disclaimer">${tr('estimate')}</p></div></main><div class="shell">${footer()}</div>`;
}

async function saveLeadFirst(){
  const name=$('#leadName').value.trim(),phone=$('#leadPhone').value.trim(),city=$('#leadCity').value.trim(),state=$('#leadState').value;
  if(!name||!phone||!city||!$('#leadConsent').checked){alert(tr('required'));return}
  const button=$('.panel-actions .btn:not(.secondary)');button.disabled=true;button.textContent='…';
  const language=lang;
  leadDetails={name,phone,email:$('#leadEmail').value.trim()||null,city,state,language,marketing_consent:$('#leadMarketing').checked,business_name:$('#businessName')?.value.trim()||null};
  try{
    const res=await fetch(`${API}/leads`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,phone,email:leadDetails.email,category,language,state,city,consent:true,marketing_consent:leadDetails.marketing_consent,business_name:leadDetails.business_name})});
    if(!res.ok)throw Error(await res.text());
    leadId=(await res.json()).id;step=2;render();window.scrollTo(0,0);
  }catch(e){alert(tr('apiError'));button.disabled=false;button.textContent=tr('continueEstimate')+' →'}
}

async function makeCalc(){
  const bill=Number($('#bill').value),city=$('#city').value.trim();
  if(!bill||bill<1||!city){alert(tr('required'));return}
  const btn=$('.panel-actions .btn:not(.secondary)');btn.disabled=true;btn.textContent='…';
  const payload={monthly_bill:bill,roof_area:Number($('#roof').value)||null,monthly_units:Number($('#units').value)||null,operating_hours:Number($('#hours')?.value||10),state:$('#state').value,city,property_type:$('#property').value,shade:$('#shade').value,language:leadDetails.language,lead_id:leadId};
  try{const r=await fetch(`${API}/calculations/${category}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!r.ok)throw Error(await r.text());calc=await r.json();step=3;render();window.scrollTo(0,0)}catch(e){alert(tr('apiError'));btn.disabled=false;btn.textContent=tr('calc')}
}

function results(){
  const cap=calc.capacity_kw,last=calc.projection[24],bars=calc.projection.filter(x=>x.year%2===1).map(x=>`<div class="bar" title="Year ${x.year}: ${money(x.net_savings)}" style="height:${Math.max(15,Math.min(100,x.net_savings/Math.max(...calc.projection.map(y=>y.net_savings))*100))}%"></div>`).join('');
  return `<div class="result-hero"><div class="eyebrow" style="color:#c5dc64">${tr('quality')}</div><h2>${tr('review')}</h2><p>${tr('loc')}: ${calc.inputs.city}, ${calc.inputs.state} · ${tr('report')}: ${calc.id.slice(0,8)}</p></div><div class="status">${tr('saved')}</div><div class="result-grid">${[[tr('capacity'),`${cap.low}–${cap.high} kW`],[tr('generation'),`${num(calc.annual_generation_kwh)} kWh`],[tr('monthly'),money(calc.monthly_savings_inr)],[lang==='te'?'అంచనా బిల్లు తగ్గింపు':'Estimated bill reduction',`${calc.bill_reduction_percent}%`],[tr('annual'),money(calc.annual_savings_inr)],[tr('cost'),money(calc.gross_cost_inr)],[tr('payback'),calc.payback_years?`${calc.payback_years} years`:'Not recoverable']].map(([a,b])=>`<article class="result-card"><span>${a}</span><b>${b}</b></article>`).join('')}</div><div class="panel"><h3>${tr('cashflow')}</h3><div class="chart">${bars}</div><p class="disclaimer">${tr('projection')}: ${money(last.cumulative_net)} · ${tr('carbon')}: ${calc.carbon_reduction_tonnes_year} tCO₂e · ${tr('subsidy')}: ${tr(category==='residential'?'notassessed':'notapp')}</p><a class="btn secondary" href="${API}/reports/${calc.id}/pdf" target="_blank" rel="noopener">Download estimate PDF ↓</a><table class="table"><thead><tr><th>${tr('year')}</th><th>${tr('cashflow')}</th><th>${tr('projection')}</th></tr></thead><tbody>${[1,5,10,15,20,25].map(y=>{const r=calc.projection[y-1];return `<tr><td>${y}</td><td>${money(r.net_savings)}</td><td>${money(r.cumulative_net)}</td></tr>`}).join('')}</tbody></table><div class="notice">${tr('subsidyNote')}<br>${calc.uncertainties.join(' ')}</div></div>`;
}

render();
