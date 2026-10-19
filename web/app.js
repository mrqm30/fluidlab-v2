/* FluidLab UI: la matemática se calcula en el motor Python. Sin dependencias externas. */
'use strict';
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const FLUIDS = {
  glycerin: {rho:1260,mu:1.49},
  water: {rho:998.2,mu:0.001002},
  air: {rho:1.204,mu:0.0000181},
  oil: {rho:870,mu:0.1}
};
const FIELDS = {
  delta:{label:'Espesor de película δ', unit:'m', note:'Espesor perpendicular a la pared'},
  beta:{label:'Inclinación β',unit:'°',note:'Ángulo medido desde la vertical'},
  width:{label:'Ancho de sistema W',unit:'m'},
  length:{label:'Longitud axial L',unit:'m'},
  radius:{label:'Radio interior R',unit:'m'},
  dp:{label:'Caída de presión ΔP',unit:'Pa',note:'p entrada − p salida'},
  half_gap:{label:'Semiseparación δ',unit:'m',note:'Distancia total entre placas = 2δ'},
  inner_radius:{label:'Radio interno Rᵢ',unit:'m'},
  outer_radius:{label:'Radio externo Rₑ',unit:'m'},
  speed:{label:'Velocidad placa superior U',unit:'m/s'},
  gap:{label:'Separación entre placas h',unit:'m'},
  area:{label:'Área de contacto A',unit:'m²'},
  speed_lower:{label:'Velocidad placa inferior U₀',unit:'m/s',note:'Positiva hacia la derecha; puede ser negativa'},
  speed_upper:{label:'Velocidad placa superior U₁',unit:'m/s',note:'Puede ser igual, menor o contraria a U₀'},
  gas_name:{label:'Gas puro',unit:'',options:[['air','Aire seco'],['nitrogen','Nitrógeno'],['oxygen','Oxígeno'],['co2','Dióxido de carbono']]},
  temperature_C:{label:'Temperatura de trabajo',unit:'°C'},
  pressure:{label:'Presión absoluta',unit:'Pa'},
  metal_name:{label:'Metal líquido',unit:'',options:[['mercury','Mercurio fundido'],['gallium','Galio fundido'],['sodium','Sodio fundido'],['custom','Otro metal (parámetros propios)']]},
  reference_C:{label:'Temperatura de referencia',unit:'°C'},
  reference_mu:{label:'Viscosidad μ de referencia',unit:'Pa·s',note:'Propiedad aproximada, reemplazar por dato tabulado'},
  reference_rho:{label:'Densidad de referencia',unit:'kg/m³'},
  activation_energy:{label:'Ea viscosidad (opcional)',unit:'J/mol',note:'0 = sin extrapolación térmica; distinto de 0 exige calibración'},
  mix_type:{label:'Tipo de mezcla binaria',unit:'',options:[['liquid','Dos líquidos miscibles'],['gas','Dos gases diluidos']]},
  fraction:{label:'Fracción del componente 1',unit:'0–1',note:'Volumétrica en líquidos; molar en gases'},
  mu1:{label:'Viscosidad del líquido 1',unit:'Pa·s'},
  mu2:{label:'Viscosidad del líquido 2',unit:'Pa·s'},
  rho1:{label:'Densidad del líquido 1',unit:'kg/m³'},
  rho2:{label:'Densidad del líquido 2',unit:'kg/m³'},
  gas_a:{label:'Gas componente 1',unit:'',options:[['nitrogen','Nitrógeno'],['oxygen','Oxígeno'],['co2','Dióxido de carbono']]},
  gas_b:{label:'Gas componente 2',unit:'',options:[['oxygen','Oxígeno'],['nitrogen','Nitrógeno'],['co2','Dióxido de carbono']]},
  orientation:{label:'Orientación axial',unit:'',note:'Sentido positivo del flujo',options:[
    ['horizontal','Horizontal'],['down','Vertical descendente'],['up','Vertical ascendente']
  ]}
};
const MODULES = {
  film:{title:'Película descendente',desc:'Balance de momento sobre una película viscosa que escurre por una superficie inclinada.',tag:'SUPERFICIE LIBRE',reference:'PÁGS. 14–24',fields:['delta','beta','width','length'],values:{delta:.0015,beta:30,width:.3,length:1.2},fluid:'glycerin',diagram:'Película con superficie libre y pared inclinada; x = 0 en el líquido-gas.'},
  pipe:{title:'Tubería circular',desc:'Resuelve Hagen–Poiseuille para un conducto circular completamente desarrollado.',tag:'HAGEN–POISEUILLE',reference:'PÁGS. 25–38',fields:['radius','length','dp','orientation'],values:{radius:.004,length:2,dp:20,orientation:'horizontal'},fluid:'water',diagram:'El fluido se mueve axialmente; la velocidad es máxima en el eje central.'},
  plates:{title:'Placas paralelas',desc:'Obtén el perfil parabólico, caudal y esfuerzo cortante de un flujo impulsado por presión.',tag:'FLUJO PLANO',reference:'PÁGS. 39–43',fields:['half_gap','width','length','dp'],values:{half_gap:.001,width:.15,length:1,dp:30},fluid:'water',diagram:'Dos paredes estacionarias separadas por 2δ; y = 0 en el plano medio.'},
  viscosity:{title:'Viscosidad de fluidos',desc:'Explora la ley de Newton de la viscosidad con una placa móvil y una placa estacionaria.',tag:'LEY DE NEWTON',reference:'AMPLIACIÓN',fields:['speed','gap','area'],values:{speed:.25,gap:.003,area:.12},fluid:'glycerin',diagram:'Flujo de Couette: una placa móvil genera un perfil de velocidad lineal.'},
  annulus:{title:'Tubos concéntricos',desc:'Simula el flujo en el espacio anular entre dos tubos coaxiales sin deslizamiento.',tag:'FLUJO ANULAR',reference:'AMPLIACIÓN',fields:['inner_radius','outer_radius','length','dp'],values:{inner_radius:.004,outer_radius:.01,length:2,dp:60},fluid:'water',diagram:'El líquido fluye entre dos paredes cilíndricas; velocidad nula en ambas.'},
  couette:{title:'Dos placas separadas',desc:'Controla por separado U₀, U₁ y ΔP: Couette puro, Poiseuille plano o combinación de ambos.',tag:'COUETTE–POISEUILLE',reference:'AMPLIACIÓN',fields:['gap','speed_lower','speed_upper','length','width','dp'],values:{gap:.003,speed_lower:0,speed_upper:.25,length:1,width:.12,dp:0},fluid:'glycerin',diagram:'Dos placas distantes h; ambas pueden moverse, y la presión puede impulsar el flujo.'},
  gas:{title:'Viscosidad de gases',desc:'Calcula μ(T) por Sutherland, ρ por gas ideal y ν; observa cómo cambian con temperatura.',tag:'GAS DILUIDO',reference:'MODELO DE SUTHERLAND',fields:['gas_name','temperature_C','pressure','speed','gap','area'],values:{gas_name:'air',temperature_C:20,pressure:101325,speed:.5,gap:.002,area:.1},fluid:null,diagram:'Un gas puro entre superficies: μ depende de T; la densidad depende de T y p.',requiresProperties:true},
  metal:{title:'Viscosidad de metales líquidos',desc:'Calcula propiedades de un metal fundido y, opcionalmente, su dependencia térmica calibrada.',tag:'METAL FUNDIDO',reference:'AMPLIACIÓN · REOLOGÍA',fields:['metal_name','temperature_C','reference_C','reference_mu','reference_rho','activation_energy','speed','gap','area'],values:{metal_name:'mercury',temperature_C:20,reference_C:20,reference_mu:.001526,reference_rho:13546,activation_energy:0,speed:.2,gap:.002,area:.1},fluid:null,diagram:'Solo metal en fase líquida. Un metal sólido no se modela con viscosidad de fluido.',requiresProperties:true},
  mixture:{title:'Viscosidad de mezclas',desc:'Mezclas binarias de líquidos miscibles (regla logarítmica) o gases diluidos (Wilke).',tag:'MEZCLAS BINARIAS',reference:'AMPLIACIÓN · MEZCLAS',fields:['mix_type','fraction','mu1','mu2','rho1','rho2'],values:{mix_type:'liquid',fraction:.35,mu1:.001002,mu2:1.49,rho1:998.2,rho2:1260},fluid:null,diagram:'Selecciona gas o líquido. La proporción es molar para gases y volumétrica para líquidos.',requiresProperties:true}

};
const MIX_GAS_DEFAULTS = {mix_type:'gas',fraction:.79,gas_a:'nitrogen',gas_b:'oxygen',temperature_C:20,pressure:101325};
const METAL_PRESETS = {mercury:{reference_C:20,temperature_C:20,reference_mu:.001526,reference_rho:13546},gallium:{reference_C:35,temperature_C:35,reference_mu:.0019,reference_rho:6095},sodium:{reference_C:120,temperature_C:120,reference_mu:.00065,reference_rho:927}};
let current='film';
let viscosityKind='dynamic';
let lastResult=null;
let chartMode='profile';
let requestSerial=0;
let toastTimeout;
const format=(n,digits=5)=>{
  if(typeof n!=='number'||!Number.isFinite(n))return String(n);
  if(n===0)return '0';
  const abs=Math.abs(n);
  if(abs<.0001||abs>=1e7)return n.toExponential(3).replace('e+','e+');
  return new Intl.NumberFormat('es-MX',{maximumSignificantDigits:digits}).format(n);
};
const rawNum=(n)=>Number(n).toPrecision(9).replace(/\.?0+$/,'').replace(/e\+?/,'e');
const esc=(s)=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(message,success=false){const el=$('#toast');el.textContent=message;el.classList.toggle('success',success);el.classList.add('visible');clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>el.classList.remove('visible'),4400);}
function updateViscosityLabel(){
  const kin=viscosityKind==='kinematic';
  $('#viscosityLabel').textContent=kin?'Viscosidad cinemática ν':'Viscosidad dinámica μ';
  $('#viscosityUnit').textContent=kin?'m²/s':'Pa·s';
  $$('[data-viscosity]').forEach(b=>b.classList.toggle('selected',b.dataset.viscosity===viscosityKind));
}
function setFluid(fluid){
  $('#fluidSelect').value=fluid;
  const f=FLUIDS[fluid];
  if(!f)return;
  $('#rho').value=f.rho;
  $('#viscosity_value').value=viscosityKind==='dynamic'?f.mu:(f.mu/f.rho);
}
function fieldKeys(kind,values){
  if(kind==='mixture' && values.mix_type==='gas')return ['mix_type','fraction','gas_a','gas_b','temperature_C','pressure'];
  return MODULES[kind].fields;
}
function renderDynamicFields(kind,values){
  const conf=MODULES[kind];
  $('#dynamicFields').innerHTML=fieldKeys(kind,values).map(key=>{
    const p=FIELDS[key];const val=values[key]??'';
    const input=p.options?`<select id="${key}" name="${key}">${p.options.map(([code,title])=>`<option value="${code}" ${val===code?'selected':''}>${esc(title)}</option>`).join('')}</select>`:`<input type="number" inputmode="decimal" step="any" id="${key}" name="${key}" value="${esc(val)}"/>`;
    return `<div class="field ${key==='orientation'?'full-width':''}"><label for="${key}">${esc(p.label)} <small>${esc(p.unit)}</small></label>${input}${p.note?`<small class="field-helper">${esc(p.note)}</small>`:''}</div>`;
  }).join('');
}
function saveState(){try{localStorage.setItem('fluidlab-user',JSON.stringify({module:current,kind:viscosityKind,fluid:$('#fluidSelect').value,values:allValues()}));}catch(e){}}
function restoreState(){try{const s=JSON.parse(localStorage.getItem('fluidlab-user')||'null');return s&&MODULES[s.module]?s:null;}catch(e){return null;}}
function allValues(){const obj={rho:$('#rho').value,viscosity_value:$('#viscosity_value').value};fieldKeys(current,{mix_type:$('#mix_type')?.value||'liquid'}).forEach(k=>obj[k]=$('#'+k).value);return obj;}
function setModule(kind,values,fluid){
  current=kind;const conf=MODULES[kind];
  $$('.nav-item[data-module]').forEach(el=>el.classList.toggle('active',el.dataset.module===kind));
  $('#breadcrumbCurrent').textContent=conf.title;
  $('#pageTitle').textContent=conf.title;
  $('#pageDescription').textContent=conf.desc;
  $('#heroTag').innerHTML='<span>◈</span> '+esc(conf.tag);
  $('#referenceLabel').textContent=conf.reference;
  const chosen=values||conf.values;
  renderDynamicFields(kind,chosen);
  $('#standardFluidInputs').hidden=Boolean(conf.requiresProperties);
  $('#parametersHeading').textContent=conf.requiresProperties?'PROPIEDADES Y CONDICIONES':'GEOMETRÍA Y OPERACIÓN';
  if(conf.fluid) setFluid(fluid||conf.fluid);
  $('#geometryNote').textContent=conf.diagram;
  $('#geometryView').innerHTML=diagram(kind);
  chartMode='profile';
  $$('[data-chart]').forEach(e=>e.classList.toggle('active',e.dataset.chart===chartMode));
  solve();
}
function diagram(kind){
  const marker='<defs><marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6Z" fill="#5fe0bc"/></marker><linearGradient id="liquid" x1="0" x2="1"><stop stop-color="#225269"/><stop offset="1" stop-color="#2a798a"/></linearGradient></defs>';
  const start='<svg viewBox="0 0 420 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagrama ilustrativo de geometría">'+marker;
  let body='';
  if(kind==='film'){
    body=`<g transform="translate(60 14) rotate(-22 180 94)"><rect class="geometry-wall" x="15" y="135" width="350" height="15" rx="3"/><rect fill="url(#liquid)" stroke="#5aa2ae" x="15" y="91" width="350" height="44"/><line x1="15" y1="91" x2="365" y2="91" stroke="#86dccc" stroke-width="2"/><path d="M32 91v44 M48 91v44" stroke="#285162" opacity=".6"/><line class="geometry-arrow" x1="105" y1="113" x2="168" y2="113" marker-end="url(#arr)"/><line class="geometry-arrow" x1="195" y1="108" x2="273" y2="108" marker-end="url(#arr)"/><text class="geometry-label" x="130" y="74">Superficie libre</text><text class="geometry-label" x="125" y="167">Pared inclinada</text></g><text class="geometry-label" x="12" y="28">↓ g</text><text class="geometry-label" x="368" y="180">β</text>`;
  }else if(kind==='pipe'){
    body=`<rect x="25" y="55" width="370" height="104" rx="5" fill="url(#liquid)"/><rect x="25" y="45" width="370" height="13" rx="4" class="geometry-wall"/><rect x="25" y="158" width="370" height="13" rx="4" class="geometry-wall"/><line x1="30" y1="107" x2="393" y2="107" stroke="#6d9fb0" stroke-dasharray="5 5"/><path d="M44 106Q70 70 106 107 Q140 141 178 107" stroke="#78debf" fill="none" stroke-width="2" opacity=".65"/><line class="geometry-arrow" x1="150" y1="108" x2="252" y2="108" marker-end="url(#arr)"/><line class="geometry-arrow" x1="150" y1="80" x2="219" y2="80" marker-end="url(#arr)"/><line class="geometry-arrow" x1="150" y1="137" x2="219" y2="137" marker-end="url(#arr)"/><text class="geometry-label" x="31" y="34">p entrada</text><text class="geometry-label" x="310" y="34">p salida</text><text class="geometry-label" x="168" y="194">Radio R</text>`;
  }else if(kind==='plates'){
    body=`<rect x="26" y="34" width="368" height="16" class="geometry-wall" rx="3"/><rect x="26" y="162" width="368" height="16" class="geometry-wall" rx="3"/><rect x="26" y="50" width="368" height="112" fill="url(#liquid)" opacity=".75"/><line x1="27" y1="105" x2="390" y2="105" stroke="#72acb5" stroke-dasharray="4 6"/><path d="M53 52q10 0 20 55q-10 55-20 55" stroke="#8be7ca" stroke-width="2" fill="none"/><line class="geometry-arrow" x1="115" y1="105" x2="286" y2="105" marker-end="url(#arr)"/><line class="geometry-arrow" x1="136" y1="76" x2="213" y2="76" marker-end="url(#arr)"/><line class="geometry-arrow" x1="136" y1="137" x2="213" y2="137" marker-end="url(#arr)"/><text class="geometry-label" x="347" y="95">δ</text><text class="geometry-label" x="320" y="200">2δ total</text>`;
  }else if(kind==='couette'){
    body=`<rect x="27" y="39" width="366" height="16" rx="3" class="geometry-wall"/><rect x="27" y="159" width="366" height="16" rx="3" class="geometry-wall"/><rect x="27" y="55" width="366" height="104" fill="url(#liquid)"/><line class="geometry-arrow" x1="95" y1="28" x2="230" y2="28" marker-end="url(#arr)"/><line class="geometry-arrow" x1="245" y1="183" x2="325" y2="183" marker-end="url(#arr)"/><path d="M50 159Q124 147 208 88T370 55" fill="none" stroke="#9af8d9" stroke-width="3" stroke-dasharray="7 4"/><text class="geometry-label" x="285" y="26">U₁</text><text class="geometry-label" x="335" y="198">U₀</text><text class="geometry-label" x="350" y="111">h</text>`;
  }else if(kind==='gas'){
    body=`<g fill="none" stroke="#6ee6c4"><circle cx="65" cy="78" r="12"/><circle cx="145" cy="137" r="13"/><circle cx="224" cy="78" r="15"/><circle cx="322" cy="135" r="12"/><circle cx="335" cy="62" r="10"/><circle cx="97" cy="154" r="10"/><circle cx="250" cy="152" r="8"/></g><g stroke="#55a9bd" stroke-width="1.4" stroke-dasharray="4 4"><path d="M68 75l36-30 45 62 72-29 56 33 45-42" fill="none"/><path d="M97 151l58-29 65 15 29 14 72-20" fill="none"/></g><text class="geometry-label" x="26" y="31">Gas ideal · T, p</text><text class="geometry-label" x="300" y="192">μ = μ(T)</text>`;
  }else if(kind==='metal'){
    body=`<rect x="27" y="46" width="365" height="120" rx="9" fill="#1f4f5b" stroke="#4b8995"/><path d="M32 80Q80 45 120 80T210 80T300 80T388 80" stroke="#b0eff0" stroke-width="3" fill="none"/><g fill="#8ee0df" opacity=".85"><circle cx="80" cy="110" r="10"/><circle cx="146" cy="127" r="12"/><circle cx="210" cy="107" r="11"/><circle cx="280" cy="130" r="13"/><circle cx="335" cy="111" r="10"/></g><text class="geometry-label" x="42" y="29">Metal fundido</text><text class="geometry-label" x="210" y="190">Estado líquido; T > fusión</text>`;
  }else if(kind==='mixture'){
    body=`<rect x="27" y="55" width="366" height="105" rx="11" fill="#254654" stroke="#638da4"/><g fill="#6debc8"><circle cx="76" cy="90" r="11"/><circle cx="140" cy="135" r="11"/><circle cx="207" cy="94" r="11"/><circle cx="293" cy="137" r="11"/><circle cx="354" cy="87" r="11"/></g><g fill="#9bb2fa"><circle cx="111" cy="112" r="10"/><circle cx="167" cy="92" r="10"/><circle cx="242" cy="132" r="10"/><circle cx="321" cy="102" r="10"/></g><text class="geometry-label" x="40" y="34">Componente 1 + componente 2</text><text class="geometry-label" x="160" y="187">Composición ajustable</text>`;
  }else if(kind==='viscosity'){
    body=`<rect x="29" y="36" width="365" height="16" rx="3" class="geometry-wall"/><rect x="29" y="164" width="365" height="16" rx="3" class="geometry-wall"/><rect x="29" y="52" width="365" height="112" fill="url(#liquid)" opacity=".7"/><line class="geometry-arrow" x1="135" y1="26" x2="315" y2="26" marker-end="url(#arr)"/><path d="M46 164L329 53" stroke="#7becc6" stroke-width="2" stroke-dasharray="5 5"/><line x1="45" y1="164" x2="49" y2="164" stroke="#7becc6"/><line class="geometry-arrow" x1="135" y1="88" x2="269" y2="88" marker-end="url(#arr)"/><line class="geometry-arrow" x1="135" y1="136" x2="195" y2="136" marker-end="url(#arr)"/><text class="geometry-label" x="39" y="20">Placa móvil → U</text><text class="geometry-label" x="38" y="198">Placa fija, v = 0</text><text class="geometry-label" x="363" y="112">h</text>`;
  }else{
    body=`<rect x="20" y="45" width="380" height="125" rx="5" fill="url(#liquid)"/><rect x="20" y="32" width="380" height="15" rx="4" class="geometry-wall"/><rect x="20" y="170" width="380" height="15" rx="4" class="geometry-wall"/><rect x="20" y="90" width="380" height="35" class="geometry-wall"/><line class="geometry-arrow" x1="85" y1="68" x2="182" y2="68" marker-end="url(#arr)"/><line class="geometry-arrow" x1="85" y1="146" x2="182" y2="146" marker-end="url(#arr)"/><text class="geometry-label" x="228" y="70">Espacio anular</text><text class="geometry-label" x="230" y="114">Tubo interior</text><text class="geometry-label" x="240" y="204">Rᵢ &lt; r &lt; Rₑ</text>`;
  }
  return start+body+'</svg>';
}
function payload(){return {module:current,viscosity_kind:viscosityKind,...allValues()};}
function renderResults(data){
  lastResult=data;
  $('#metricsGrid').innerHTML=data.metrics.map((m,i)=>`<div class="metric"><div class="metric-label">${esc(m.label)}</div><div class="metric-val"><strong>${esc(format(m.value))}</strong><small>${esc(m.unit)}</small></div><div class="metric-note">${esc(m.note)}</div></div>`).join('');
  $('#regimeCard').className='regime-card '+data.regime.tone;
  $('#regimeTitle').textContent=data.regime.title;
  $('#regimeDetail').textContent=data.regime.detail;
  const re=data.metrics.find(m=>m.label.toLowerCase().includes('reynolds'));
  $('#regimeRe').textContent=re?'Re = '+format(re.value):'';
  $('#equationsList').innerHTML=data.equations.map(e=>`<div class="equation"><label>${esc(e.label)}</label><code>${esc(e.formula)}</code></div>`).join('');
  $('#stepsList').innerHTML=data.steps.map(s=>`<div class="step"><div><strong>${esc(s.title)}</strong><p>${esc(s.detail)}</p></div></div>`).join('');
  $('#observationsList').innerHTML=data.observations.map(s=>`<li>${esc(s)}</li>`).join('');
  $('#modelNotice').textContent=data.model_notice+' · '+data.source;
  const chartNames=data.chart_labels||['Perfil de velocidad','Esfuerzo cortante'];
  $('[data-chart="profile"]').textContent=chartNames[0];
  $('[data-chart="stress"]').textContent=chartNames[1];
  $('.chart-header h2').textContent=(data.module==='gas'||data.module==='metal'||data.module==='mixture')?'Propiedades físicas':'Perfiles de flujo';
  $('#calculatedFlag').innerHTML='<span>●</span> Calculado';
  drawChart();
}
function drawChart(){
  const svg=$('#graph');if(!lastResult)return;
  const d=lastResult[chartMode];const pts=d.points;
  const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);
  let xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
  if(xmax===xmin){xmax=xmin+1;}
  if(ymin===0&&ymax===0){ymax=1;}
  if(ymin>=0){ymin=0;ymax*=1.12;}
  else if(ymax<=0){ymax=0;ymin*=1.12;}
  else {const pady=(ymax-ymin)*.12;ymin-=pady;ymax+=pady;}
  const L=86,R=18,T=28,B=58,W=780-L-R,H=305-T-B;
  const x=(val)=>L+(val-xmin)/(xmax-xmin)*W;
  const y=(val)=>T+(ymax-val)/(ymax-ymin)*H;
  const titleX=d.x_label+' ('+d.x_unit+')';
  const titleY=d.y_label+' ('+d.y_unit+')';
  let out='<defs><linearGradient id="curveFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5fe0bc" stop-opacity=".30"/><stop offset="1" stop-color="#5fe0bc" stop-opacity=".012"/></linearGradient></defs>';
  for(let i=0;i<=4;i++){
    const frac=i/4, vy=ymin+(ymax-ymin)*frac,yy=y(vy);
    out+=`<line x1="${L}" y1="${yy}" x2="${L+W}" y2="${yy}" stroke="#314357" stroke-dasharray="3 6" opacity=".9"/><text x="${L-13}" y="${yy+4}" font-size="12" fill="#8ca2b6" text-anchor="end">${esc(format(vy,3))}</text>`;
    const vx=xmin+(xmax-xmin)*frac,xx=x(vx);
    out+=`<text x="${xx}" y="${T+H+23}" font-size="12" fill="#8ca2b6" text-anchor="middle">${esc(format(vx,3))}</text>`;
  }
  out+=`<line x1="${L}" y1="${T}" x2="${L}" y2="${T+H}" stroke="#52708a"/><line x1="${L}" y1="${T+H}" x2="${L+W}" y2="${T+H}" stroke="#52708a"/>`;
  const line=pts.map((p,i)=>(i===0?'M':'L')+x(p[0]).toFixed(2)+','+y(p[1]).toFixed(2)).join(' ');
  const zero=y(Math.max(ymin,Math.min(ymax,0)));
  const area=line+` L${x(pts.at(-1)[0]).toFixed(2)},${zero.toFixed(2)} L${x(pts[0][0]).toFixed(2)},${zero.toFixed(2)} Z`;
  out+=`<path d="${area}" fill="url(#curveFill)"/><path d="${line}" fill="none" stroke="#66e6c0" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>`;
  const peak=pts.reduce((a,b)=>Math.abs(b[1])>Math.abs(a[1])?b:a,pts[0]);
  const px=x(peak[0]),py=y(peak[1]);
  out+=`<circle cx="${px}" cy="${py}" r="5.5" fill="#8bf8d4" stroke="#112e34" stroke-width="2"/><text x="${Math.min(L+W-5,Math.max(L+5,px+11))}" y="${Math.max(15,py-14)}" font-size="12" fill="#bdf9e4">${esc(format(peak[1],4))}</text>`;
  out+=`<text x="${L+W/2}" y="${302}" font-size="12" fill="#94acbe" text-anchor="middle">${esc(titleX)}</text>`;
  out+=`<text transform="translate(18 ${T+H/2}) rotate(-90)" font-size="12" text-anchor="middle" fill="#94acbe">${esc(titleY)}</text>`;
  svg.innerHTML=out;
  $('#chartFootnote').textContent=(chartMode==='profile'?d.y_label:lastResult.stress.y_label)+' · '+pts.length+' puntos · Modelo '+(lastResult.module==='mixture'?'aproximado':'analítico');
}
async function solve(){
  const seq=++requestSerial;const btn=$('#btnCalculate');btn.disabled=true;$('#calculatedFlag').textContent='Calculando...';
  try{
    const response=await fetch('/api/calculate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});
    const data=await response.json();
    if(seq!==requestSerial)return;
    if(!response.ok)throw new Error(data.error||'No fue posible calcular.');
    renderResults(data);saveState();
  }catch(err){if(seq===requestSerial){$('#calculatedFlag').textContent='Error de cálculo';toast(err.message||'Error de comunicación. ¿Está ejecutándose el servidor?');}}
  finally{if(seq===requestSerial)btn.disabled=false;}
}
function downloadCSV(){
  if(!lastResult){toast('Calcula primero el perfil.');return;}
  const a=lastResult.profile.points,b=lastResult.stress.points;
  const lines=[[lastResult.profile.x_label+' ('+lastResult.profile.x_unit+')',lastResult.profile.y_label+' ('+lastResult.profile.y_unit+')',lastResult.stress.y_label+' ('+lastResult.stress.y_unit+')'].map(x=>'"'+String(x).replaceAll('"','""')+'"').join(',')];
  a.forEach((p,i)=>lines.push([p[0],p[1],b[i][1]].map(v=>Number(v).toPrecision(12)).join(',')));
  const blob=new Blob(['\ufeff'+lines.join('\r\n')],{type:'text/csv;charset=utf-8;'});
  const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download='fluidlab_'+current+'_perfil.csv';document.body.appendChild(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Datos del perfil exportados a CSV.',true);
}
function bind(){
  $$('#moduleNav [data-module]').forEach(el=>el.addEventListener('click',()=>setModule(el.dataset.module)));
  $('#fluidSelect').addEventListener('change',e=>{if(FLUIDS[e.target.value])setFluid(e.target.value);solve();});
  $$('[data-viscosity]').forEach(btn=>btn.addEventListener('click',()=>{
    const next=btn.dataset.viscosity;if(next===viscosityKind)return;
    const rho=Number($('#rho').value),value=Number($('#viscosity_value').value);
    if(Number.isFinite(rho)&&rho>0&&Number.isFinite(value)&&value>0){$('#viscosity_value').value=next==='kinematic'?value/rho:value*rho;}
    viscosityKind=next;updateViscosityLabel();solve();
  }));
  $('#dynamicFields').addEventListener('change',ev=>{
    if(ev.target.id==='mix_type'){
      const mode=ev.target.value;
      renderDynamicFields('mixture',mode==='gas'?MIX_GAS_DEFAULTS:MODULES.mixture.values);
    }else if(ev.target.id==='metal_name'){
      const preset=METAL_PRESETS[ev.target.value];
      if(preset){for(const [key,val] of Object.entries(preset))$('#'+key).value=val;$('#activation_energy').value=0;}
    }
    solve();
  });
  $('#btnCalculate').addEventListener('click',solve);
  $('#btnReset').addEventListener('click',()=>{viscosityKind='dynamic';updateViscosityLabel();setModule(current);toast('Valores de ejemplo restaurados.',true);});
  $$('[data-chart]').forEach(el=>el.addEventListener('click',()=>{chartMode=el.dataset.chart;$$('[data-chart]').forEach(t=>t.classList.toggle('active',t===el));drawChart();}));
  $('#btnCSV').addEventListener('click',downloadCSV);
  $('#rho').addEventListener('change',()=>{$('#fluidSelect').value='manual';});
  $('#viscosity_value').addEventListener('change',()=>{$('#fluidSelect').value='manual';});
  document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key==='Enter'){event.preventDefault();solve();}});
}
(function init(){bind();const state=restoreState();const fromUrl=new URLSearchParams(location.search).get('module');if(fromUrl&&MODULES[fromUrl]){setModule(fromUrl);return;}if(state){viscosityKind=state.kind==='kinematic'?'kinematic':'dynamic';updateViscosityLabel();setModule(state.module,state.values,state.fluid);$('#rho').value=state.values.rho;$('#viscosity_value').value=state.values.viscosity_value;solve();}else{setModule('film');}})();
