'use strict';
$('toggleFilters').onclick=()=>{const expanded=$('filtersPanel').classList.toggle('expanded');$('toggleFilters').setAttribute('aria-expanded',String(expanded));$('toggleFilters').textContent=expanded?'收起筛选':'展开筛选';};
// Human editing and interchange use exactly the same preview/apply APIs as ai.py.
const FIELD_LABELS = {name:'显示名称',function:'用途摘要',details:'完整说明',compatibility:'兼容说明',risk:'风险说明',variantRule:'变体规则',group:'用途分类',tags:'标签（每行一个）',description:'文件说明',version:'文件版本',category:'文件类别'};

async function editResource(id) {
  const resource = await api('/api/resource?id='+encodeURIComponent(id));
  const keys = Object.keys(resource.editableFields).filter(k=>k!=='requirements');
  const fields = keys.map(k=>`<label>${esc(FIELD_LABELS[k]||k)}<textarea name="${k}" rows="${k==='details'?8:2}">${esc(k==='tags'?(resource.data[k]||[]).join('\n'):resource.data[k]||'')}</textarea></label>`).join('');
  const result = await form('整理资料 · 保留来源与修改历史', fields+'<label>修改说明<input name="note" placeholder="例如：补充作者提供的变体规则"></label>');
  if(!result)return;
  const patch={};
  for(const k of keys){const value=k==='tags'?result[k].split('\n').map(x=>x.trim()).filter(Boolean):result[k];if(JSON.stringify(value)!==JSON.stringify(resource.data[k]??(k==='tags'?[]:'')))patch[k]=value;}
  if(!Object.keys(patch).length){toast('没有修改');return;}
  const preview=await api('/api/content/preview',{records:[{resourceId:id,baseRevision:resource.revision,patch,note:result.note||'界面整理资料'}]});
  if(preview.errors.length)throw new Error(preview.errors[0].error);
  await api('/api/content/apply',{previewId:preview.previewId});
  if(state.detail){state.detail=await api('/api/mod?id='+encodeURIComponent(state.detail.id));await refreshDetail();}
  await facets();if(['browse','favorites','recent'].includes(state.view))await browse();
  toast('资料已保存，可在修改记录中恢复');
}

function renderProfileImport() {
  const panel=document.createElement('section');panel.className='panel';
  panel.innerHTML='<h2>导入已有搭配</h2><p>选择本应用导出的 JSON 清单，先核对具体文件与副本，再保存为新搭配。</p><label>搭配清单<input id="profileImportFile" type="file" accept=".json"></label><div id="profileImportPreview"></div>';
  $('profilesView').append(panel);
  $('profileImportFile').onchange=()=>action(async()=>{
    const file=$('profileImportFile').files[0];if(!file)return;
    if(file.size>30*1024*1024)throw new Error('清单不能超过 30 MiB');
    const p=await api('/api/profile/preview',{manifest:JSON.parse(await file.text())});
    $('profileImportPreview').innerHTML=`<p>可导入 ${p.valid} 个文件，${p.errors.length} 项需要处理。</p>${p.errors.map(e=>`<p class="status-error">${esc(e.fileId)}：${esc(e.error)}</p>`).join('')}<label>新搭配名称<input id="importProfileName" value="${esc(p.suggestedName)}" maxlength="120"></label><button id="applyProfileImport" class="primary">保存合格项为新搭配</button>`;
    $('applyProfileImport').onclick=()=>action(async()=>{const result=await api('/api/profile/import',{previewId:p.previewId,name:$('importProfileName').value});await profilesView();await showProfile(result.id);toast('搭配已导入');});
  });
}

function renderContentInterchange() {
  const panel=document.createElement('section');panel.className='panel';
  panel.innerHTML='<h2>资料导入与导出</h2><p>导出当前游戏（未选游戏时导出全部）的原文、文件资料、修订号和现有译文。AI 按数据契约生成修改记录后，可在此校验并导入。</p><button id="exportContent">导出资料 JSONL</button><label>修改记录文件（JSON 数组或 JSONL）<input id="contentEditsFile" type="file" accept=".json,.jsonl"></label><div id="contentEditsPreview"></div><p><a href="/api/schema" target="_blank" rel="noopener">查看 JSON Schema 数据契约</a></p>';
  $('settingsView').append(panel);
  $('exportContent').onclick=()=>action(async()=>{const out=await api('/api/content/export',{game:state.game});download(out.download);});
  $('contentEditsFile').onchange=()=>action(async()=>{
    const f=$('contentEditsFile').files[0];if(!f)return;if(f.size>30*1024*1024)throw new Error('请将修改记录拆分到 30 MiB 以内');
    const raw=(await f.text()).replace(/^\uFEFF/,'').trim();
    let parsed;try{parsed=JSON.parse(raw);}catch{parsed=raw.split(/\r?\n/).filter(x=>x.trim()).map(x=>JSON.parse(x));}
    const p=await api('/api/content/preview',{records:Array.isArray(parsed)?parsed:parsed.records||[parsed]});
    $('contentEditsPreview').innerHTML=`<p>可修改 ${p.valid} 个资源；${p.errors.length} 项未通过。</p>${p.changes.map(c=>`<p>${esc(c.resourceId)}：${esc(c.fields.map(k=>FIELD_LABELS[k]||k).join('、'))}</p>`).join('')}${p.errors.map(e=>`<p class="status-error">${esc(e.resourceId)}：${esc(e.error)}</p>`).join('')}<button id="applyContentEdits" class="primary" ${p.valid?'':'disabled'}>提交合格项</button>`;
    $('applyContentEdits').onclick=()=>action(async()=>{const out=await api('/api/content/apply',{previewId:p.previewId});$('applyContentEdits').disabled=true;toast('已更新 '+out.updated+' 个资源');});
  });
}
