const API_BASE_URL = window.API_BASE_URL || (location.protocol === "file:" ? "http://localhost:8000/api" : "/api");
const $ = id => document.getElementById(id);
let currentJob=null, allProducts=[], grouped=false, pollTimer=null;

function toast(msg){$("toast").textContent=msg;$("toast").classList.add("show");setTimeout(()=>$("toast").classList.remove("show"),3200)}
async function api(path, options={}){const r=await fetch(API_BASE_URL+path,options);if(!r.ok){let d={};try{d=await r.json()}catch{}throw new Error(d.detail||`HTTP ${r.status}`)}return r.json()}

async function loadCategories(){
  try{
    const d=await api("/categories"); const s=$("category");s.innerHTML="<option value=''>Select Category</option>";
    d.categories.forEach(x=>{const o=document.createElement("option");o.value=x.name;o.textContent=x.name;s.appendChild(o)});
    if(!d.categories.length) toast("No categories were exposed by the public source.");
  }catch(e){$("category").innerHTML="<option>Select Category</option>";toast(e.message)}
}
async function loadSegments(){
  $("gender").disabled=true;$("ptype").disabled=true;
  try{const d=await api(`/categories/${encodeURIComponent($("category").value)}/segments`);fill("gender",d.options,"Select Gender / Segment");$("gender").disabled=false}catch(e){toast(e.message)}
}
async function loadTypes(){
  $("ptype").disabled=true;
  try{const d=await api(`/categories/${encodeURIComponent($("category").value)}/segments/${encodeURIComponent($("gender").value)}/products`);fill("ptype",d.options,"Select Product Type");$("ptype").disabled=false}catch(e){toast(e.message)}
}
function fill(id,items,placeholder){const s=$(id);s.innerHTML="";const p=document.createElement("option");p.value="";p.textContent=placeholder;s.appendChild(p);[...new Set(items)].forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;s.appendChild(o)})}

$("category").addEventListener("change",loadSegments);$("gender").addEventListener("change",loadTypes);
$("limit").addEventListener("change",()=>{$("customLimit").hidden=$("limit").value!=="Custom"});
$("theme").onclick=()=>{document.body.classList.toggle("dark");localStorage.theme=document.body.classList.contains("dark")?"dark":"light"};
if(localStorage.theme==="dark")document.body.classList.add("dark");

$("collect").onclick=async()=>{
  if(!$("category").value||!$("gender").value||!$("ptype").value){toast("Select category, gender and product type first.");return}
  const limit=$("limit").value==="Custom"?Number($("customLimit").value):Number($("limit").value);
  if(!limit||limit<1){toast("Enter a valid product limit.");return}
  try{
    const d=await api("/collection/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({category:$("category").value,gender:$("gender").value,product_type:$("ptype").value,limit})});
    currentJob=d.job_id;$("jobPanel").classList.remove("hidden");$("jobId").textContent=currentJob;poll();
  }catch(e){toast(e.message)}
};
async function poll(){
  if(!currentJob)return; try{const d=await api(`/collection/${currentJob}`);renderJob(d);
    if(["completed","failed","blocked"].includes(d.status)){await loadProducts();$("excel").disabled=d.status!=="completed";$("pdf").disabled=d.status!=="completed";return}
  }catch(e){toast(e.message)} pollTimer=setTimeout(poll,900);
}
function renderJob(d){
  $("jobStatus").textContent=d.status.toUpperCase();$("jobStage").textContent=d.stage||"Working";
  $("discovered").textContent=d.discovered??0;$("collected").textContent=d.collected??0;$("missing").textContent=d.missing_fields??0;$("errors").textContent=d.errors??0;
  const p=Math.min(100,Number(d.progress||0)/(Number(d.discovered||d.progress||1))*100);$("bar").style.width=(isFinite(p)?p:0)+"%";$("jobProgress").textContent=(d.progress||0)+" products";
  $("jobMessage").textContent=d.error||d.message||d.current||"Collecting…";
}
async function loadProducts(){
  let page=1;allProducts=[];
  while(true){const d=await api(`/collection/${currentJob}/products?page=${page}&page_size=500`);allProducts.push(...d.items);if(allProducts.length>=d.total||!d.items.length)break;page++}
  renderProducts();
}
function money(v){return v==null?"Not Available":"₹"+Number(v).toLocaleString("en-IN")}
function cell(v){return v==null||v===""?"Not Available":v}
function renderProducts(){
  const q=$("search").value.toLowerCase();let list=allProducts.filter(p=>Object.values(p).some(v=>String(v??"").toLowerCase().includes(q)));
  if(grouped) list=[...list].sort((a,b)=>String(a.brand).localeCompare(String(b.brand)));
  $("tbody").innerHTML=list.length?list.map((p,i)=>`<tr>
<td>${i+1}</td><td>${esc(p.brand)}</td><td>${esc(p.product_name)}</td><td>${esc(p.product_id)}</td>
<td>${money(p.mrp)}</td><td>${money(p.selling_price)}</td><td>${p.discount_percentage==null?"Not Available":p.discount_percentage+"%"}</td>
<td>${p.rating==null?"Not Available":p.rating+" ★"}</td><td>${cell(p.ratings_count)}</td><td>${cell(p.reviews_count)}</td><td>${cell(p.verified_buyers)}</td>
<td>${cell(p.five_star_count)}</td><td>${cell(p.four_star_count)}</td><td>${cell(p.three_star_count)}</td><td>${cell(p.two_star_count)}</td><td>${cell(p.one_star_count)}</td>
<td>${esc(p.seller)}</td><td>${esc(p.category)}</td><td>${esc(p.gender)}</td><td>${esc(p.product_type)}</td>
<td>${p.product_url!=="Not Available"?`<a href="${esc(p.product_url)}" target="_blank" rel="noopener">Open</a>`:"Not Available"}</td><td>${new Date(p.collected_at).toLocaleString()}</td></tr>`).join(""):`<tr><td colspan="22" class="empty">No matching real data.</td></tr>`;
}
function esc(v){return String(v??"Not Available").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
$("search").oninput=renderProducts;$("group").onclick=()=>{grouped=!grouped;$("group").textContent=grouped?"Normal Table":"Group by Brand";renderProducts()};
$("excel").onclick=async()=>{await api(`/collection/${currentJob}/export/excel`,{method:"POST"});location.href=API_BASE_URL+`/collection/${currentJob}/export/excel/download`};
$("pdf").onclick=async()=>{await api(`/collection/${currentJob}/export/pdf`,{method:"POST"});location.href=API_BASE_URL+`/collection/${currentJob}/export/pdf/download`};
loadCategories();
