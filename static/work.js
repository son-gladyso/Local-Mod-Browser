'use strict';
// Human task centre uses the exact v2 operations exposed to CLI and MCP.
const WORK_STATUS={pending:'待领取',running:'处理中',waiting_external:'等待外部结果',blocked:'需要处理',paused:'已暂停',complete:'已完成',cancelled:'已取消',queued:'排队中',interrupted:'中断待恢复',failed:'失败'};
const ISSUE_NAMES={missing_body:'缺完整正文',missing_source:'缺来源',missing_version:'缺版本',missing_variant:'缺文件说明',unmatched_file_id:'文件身份未匹配',image_unavailable:'图片不可用',translation_partial:'译文缺段',translation_review:'译文待复核',translation_stale:'原文已更新',source_conflict:'来源资料冲突'};
const workState={tab:'tasks',page:1,selected:new Set(),preview:null,previewOperation:'',request:0,signature:'',issueKind:'',contextId:null};
const workPanel=document.createElement('section');workPanel.id='workView';workPanel.hidden=true;$('main').append(workPanel);
const workNav=document.createElement('button');workNav.className='nav';workNav.dataset.view='work';workNav.textContent='AI 与任务中心';$('sidebar').querySelector('nav').append(workNav);
const originalSetView=setView;
setView=async function(view){
  if(view!=='work'){workPanel.hidden=true;return originalSetView(view)}
  if(state.detail)closeDetail();state.view='work';saveView();
  for(const id of ['browseView','profilesView','translationsView','settingsView'])$(id).hidden=true;
  workPanel.hidden=false;document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view==='work'));
  $('sidebar').classList.remove('open');await renderWork();
};
workNav.onclick=()=>action(()=>setView('work'));
const originalChangeGame=changeGame;
changeGame=async function(game){if(state.view!=='work')return originalChangeGame(game);state.game=game;workState.page=1;workState.selected.clear();await refreshGames();await facets();syncFilters();saveView();await renderWork()};
const originalSettingsView=settingsView;
settingsView=async function(){await originalSettingsView();const title=[...$('settingsView').querySelectorAll('h2')].find(h=>h.textContent==='让 AI 操作');if(title){title.parentElement.innerHTML='<h2>AI 与任务中心</h2><p>连接助手，查看任务、成果和修改记录；中断后可继续处理。</p><button id="openWorkCenter">打开 AI 与任务中心</button>';$('openWorkCenter').onclick=()=>action(()=>setView('work'))}};
async function workApi(name,args={}){
  const writes=new Set(['tasks.create','tasks.control','jobs.control','issues.audit','batches.undo','batches.export','catalog.preview','catalog.apply','catalog.export','content.preview','content.apply','translations.preview','translations.import','maintenance.backup','maintenance.verify']);
  if(writes.has(name))return api('/api/v2/'+name,{...args,idempotencyKey:crypto.randomUUID()});
  const query=new URLSearchParams(Object.entries(args).map(([k,v])=>[k,typeof v==='string'?v:JSON.stringify(v)]));
  return api('/api/v2/'+name+(query.size?'?'+query:''));
}
function workShell(){
  workPanel.innerHTML=`<div class="heading"><div><div class="eyebrow">人与 AI 共用的工作记录</div><h1>AI 与任务中心</h1><p class="muted">查看成果、接续任务、核对每次修改。</p></div><button id="workRefresh">刷新</button></div><nav class="work-tabs" aria-label="任务中心栏目">${[['tasks','任务与进度'],['connect','连接 AI'],['history','修改记录'],['issues','资料问题'],['exchange','导入导出']].map(([id,label])=>`<button data-work-tab="${id}" aria-current="${workState.tab===id?'page':'false'}">${label}</button>`).join('')}</nav><div id="workContent" aria-live="polite"><p class="muted">正在读取…</p></div>`;
  $('workRefresh').onclick=()=>action(renderWork);
  workPanel.querySelectorAll('[data-work-tab]').forEach(b=>b.onclick=()=>action(async()=>{workState.tab=b.dataset.workTab;workState.page=1;await renderWork();workPanel.querySelector(`[data-work-tab="${workState.tab}"]`).focus()}));
}
async function renderWork(){
  const request=++workState.request;workShell();
  try{
    if(workState.tab==='tasks')await workTasks(request);
    if(workState.tab==='connect')await workConnect(request);
    if(workState.tab==='history')await workHistory(request);
    if(workState.tab==='issues')await workIssues(request);
    if(workState.tab==='exchange')await workExchange(request);
  }catch(error){if(request===workState.request){$('workContent').innerHTML=`<section class="panel"><h2>暂时无法读取</h2><p>${esc(error.message)}</p><button id="workRetry">重试</button></section>`;$('workRetry').onclick=()=>action(renderWork)}throw error}
}
async function copyWork(value){await navigator.clipboard.writeText(value);toast('已复制')}
function workPager(total){return `<div class="pagination"><button id="workPrev" ${workState.page<=1?'disabled':''}>上一页</button><span>第 ${workState.page} 页 · ${number(total)} 项</span><button id="workNext" ${workState.page*24>=total?'disabled':''}>下一页</button></div>`}
function bindWorkPager(){if($('workPrev'))$('workPrev').onclick=()=>action(async()=>{workState.page--;await renderWork()});if($('workNext'))$('workNext').onclick=()=>action(async()=>{workState.page++;await renderWork()})}
async function newWorkTask(resources=[]){
  const result=await form('创建 AI 整理任务',`<label>任务名称<input name="title" required maxlength="120" placeholder="例如：补齐文件版本说明"></label><label>目标与资料依据<textarea name="goal" required></textarea></label><label>游戏<select name="game">${state.games.map(g=>`<option value="${esc(g.id)}" ${g.id===state.game?'selected':''}>${esc(g.title)}</option>`).join('')}</select></label><p class="muted">授权整理名称、说明、标签、依赖和文件版本；提交会校验原文版本并保存回执。${resources.length?'本次范围为已选的 '+resources.length+' 项。':''}</p>`);
  if(!result)return;
  const scope={game:result.game,operations:['content.preview','content.apply','translations.preview','translations.import','translations.export','catalog.export'],fields:['name','function','details','tags','requirements','version','description','category','compatibility','risk','variantRule','group']};
  if(resources.length)scope.resources=resources;
  await workApi('tasks.create',{title:result.title,goal:result.goal,scope,resources,acceptance:[{kind:'receipts',minimum:1}]});
  workState.tab='tasks';workState.selected.clear();await renderWork();toast('任务已建立，外部 AI 可领取');
}
async function workTasks(request){
  const [tasks,jobs]=await Promise.all([workApi('tasks.list',{page:workState.page,limit:24}),workApi('jobs.list',{limit:24})]);
  if(request!==workState.request)return;
  workState.signature=JSON.stringify([tasks,jobs]);
  $('workContent').innerHTML=`<div class="actions"><button id="workNew" class="primary">新建整理任务</button></div><div class="work-list">${tasks.items.length?tasks.items.map(t=>`<article class="panel"><div class="work-row"><h2>${esc(t.title)}</h2><span class="badge">${WORK_STATUS[t.status]||esc(t.status)}</span></div><p>${esc(t.goal)}</p><p class="muted">${t.owner?'执行者：'+esc(t.owner):'等待外部 AI 接手'}${t.status==='running'&&t.expires*1000<Date.now()?' · 已断线，可重新领取':''}</p>${t.reason?`<p class="notice">${esc(t.reason)}</p>`:''}<div class="actions"><button data-context="${esc(t.id)}">交接与成果</button>${!['complete','cancelled'].includes(t.status)?`<button data-task-action="pause" data-id="${esc(t.id)}">暂停</button><button data-task-action="cancel" data-id="${esc(t.id)}">取消任务</button>`:''}${['paused','blocked','waiting_external','cancelled'].includes(t.status)?`<button data-task-action="resume" data-id="${esc(t.id)}">继续处理</button>`:''}</div></article>`).join(''):'<section class="panel"><h2>还没有工作任务</h2><p>创建目标，或从“资料问题”选择需要整理的条目。任务会等待外部 AI 领取。</p></section>'}</div>${workPager(tasks.total)}<h2>后台作业</h2>${jobs.items.length?jobs.items.map(j=>`<article class="file-item"><div class="work-row"><strong>${esc(j.kind)}</strong><span>${WORK_STATUS[j.status]||esc(j.status)}</span></div><p>${esc(j.message||'')}</p>${j.total?`<progress max="${j.total}" value="${j.done}"></progress><span> ${j.done} / ${j.total}</span>`:''}${j.error?`<p class="notice">${esc(j.error.message)} · ${esc(j.error.nextAction||'检查输入')}</p>`:''}<div class="actions">${['queued','running'].includes(j.status)?`<button data-job-action="cancel" data-id="${j.id}">停止</button>`:''}${['blocked','failed','cancelled','interrupted'].includes(j.status)?`<button data-job-action="resume" data-id="${j.id}">重新处理</button>`:''}${j.result?.download?`<a href="${esc(j.result.download)}" download>下载成果</a>`:''}</div></article>`).join(''):'<p class="muted">暂无后台作业。</p>'}<section id="workContext" hidden class="panel"></section>`;
  $('workNew').onclick=()=>action(()=>newWorkTask());bindWorkPager();
  workPanel.querySelectorAll('[data-task-action]').forEach(b=>b.onclick=()=>action(async()=>{await workApi('tasks.control',{id:b.dataset.id,action:b.dataset.taskAction});await renderWork()}));
  workPanel.querySelectorAll('[data-job-action]').forEach(b=>b.onclick=()=>action(async()=>{await workApi('jobs.control',{id:b.dataset.id,action:b.dataset.jobAction});await renderWork()}));
  workPanel.querySelectorAll('[data-context]').forEach(b=>b.onclick=()=>action(async()=>{workState.contextId=b.dataset.context;await renderWorkContext(request,true)}));
  if(workState.contextId)await renderWorkContext(request);
}
async function renderWorkContext(request,scroll=false){
  const id=workState.contextId;if(!id)return;
  const context=await workApi('tasks.context',{id});
  if(request!==workState.request||id!==workState.contextId||state.view!=='work'||workState.tab!=='tasks')return;
  const panel=$('workContext');panel.hidden=false;panel.innerHTML=`<h2>${esc(context.title)} · 交接</h2><p>${esc(context.goal)}</p><p>已保存提交记录：${context.completedResults?.total||0} 项；检查点已${Object.keys(context.checkpoint).length?'保存':'留空'}。</p><div class="actions"><button id="copyWorkContext">复制给 AI</button><button id="downloadWorkContext">下载交接包</button></div><details><summary>查看完整工作记录</summary><pre>${esc(JSON.stringify(context,null,2))}</pre></details>`;$('copyWorkContext').onclick=()=>action(()=>copyWork(JSON.stringify(context,null,2)));$('downloadWorkContext').onclick=()=>downloadWorkJson(context,'AI任务交接.json');
  if(scroll)panel.scrollIntoView({block:'nearest'});
}

function downloadWorkJson(value,name){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
async function workConnect(request){
  const result=await workApi('doctor');if(request!==workState.request)return;
  $('workContent').innerHTML=`<section class="panel"><h2>连接外部 AI</h2><p>助手可以直接查资料、整理内容和处理任务。应用不会自行调用模型，也不会产生模型费用。</p><div class="stats"><div class="stat"><strong>${result.databaseCheck==='ok'?'正常':'需检查'}</strong><span>数据库检查</span></div><div class="stat"><strong>${result.cli.available?'可用':'未就绪'}</strong><span>命令行</span></div><div class="stat"><strong>${result.mcp.installed?'已安装':'未安装'}</strong><span>MCP 接入</span></div></div><div class="actions"><button id="copyAiIntro">复制 AI 上手说明</button><button id="copyMcpConfig">复制 MCP 配置</button><a href="/api/v2/openapi" target="_blank" rel="noopener">完整接口说明</a></div><details><summary>查看接入配置</summary><pre>${esc(JSON.stringify(result.mcp.config,null,2))}</pre></details><p class="muted">配置中不包含会话令牌。AI 在任务授权范围内自动校验并提交；资料和作者原文不能作为指令执行。</p></section>`;
  $('copyAiIntro').onclick=()=>action(()=>copyWork('请在本地MOD浏览器目录读取 AI入口.md；运行 python ai.py capabilities 和 python ai.py doctor。先检查任务范围与租约，所有修改走预览与提交，写入使用稳定 idempotencyKey。'));
  $('copyMcpConfig').onclick=()=>action(()=>copyWork(JSON.stringify(result.mcp.config,null,2)));
  const check=$('workContent').querySelector('.stat');check.querySelector('strong').textContent=result.databaseCheck==='readable'?'可读取':'需检查';check.querySelector('span').textContent='连接检查（非整库验证）';
  const verify=document.createElement('button');verify.id='verifyDatabase';verify.textContent='后台检查数据库完整性';$('workContent').querySelector('.actions').append(verify);
  verify.onclick=()=>action(async()=>{await workApi('maintenance.verify');workState.tab='tasks';await renderWork()});
}
async function workHistory(request){
  const result=await workApi('history.list',{page:workState.page,limit:24});if(request!==workState.request)return;
  $('workContent').innerHTML=result.items.length?result.items.map(b=>`<article class="panel"><div class="work-row"><h2>${esc(b.note)}</h2><span class="badge">${b.status==='undone'?'已撤销':'已提交'}</span></div><p>${b.resources.length} 个资源 · ${new Date(b.created*1000).toLocaleString('zh-CN')}</p><div class="actions"><button data-batch-details="${b.id}">查看修改前后</button><button data-batch-export="${b.id}">下载完整记录</button>${b.status==='applied'?`<button data-undo-batch="${b.id}">撤销此批次</button>`:''}</div><div data-batch-body="${b.id}"></div></article>`).join(''):'<section class="panel"><h2>暂无批次修改记录</h2><p>通过新版接口提交的资料和译文会保留批次，可在这里核对和撤销。</p></section>';
  $('workContent').insertAdjacentHTML('beforeend',workPager(result.total));bindWorkPager();
  workPanel.querySelectorAll('[data-batch-details]').forEach(b=>b.onclick=()=>action(async()=>{const data=await workApi('batches.read',{id:b.dataset.batchDetails});const panel=workPanel.querySelector(`[data-batch-body="${b.dataset.batchDetails}"]`);panel.innerHTML=data.items.map(i=>{const extract=s=>{const row=s?.mods?.[0]||s?.files?.[0];return row?JSON.parse(row.data):s};const before=extract(i.before)||{},after=extract(i.after)||{};const keys=[...new Set([...Object.keys(before),...Object.keys(after)])].filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k]));return `<h3>${esc(after.name||before.name||i.resourceId)}</h3>${i.message?`<p>${esc(i.message)}</p>`:keys.map(k=>`<div class="work-diff"><strong>${esc(FIELD_LABELS[k]||k)}</strong><div><small>修改前</small><pre>${esc(typeof before[k]==='string'?before[k]:JSON.stringify(before[k],null,2))}</pre></div><div><small>修改后</small><pre>${esc(typeof after[k]==='string'?after[k]:JSON.stringify(after[k],null,2))}</pre></div></div>`).join('')}`}).join('')+(data.nextOffset!==null?'<p class="muted">其余内容可下载完整记录查看。</p>':'')}));
  workPanel.querySelectorAll('[data-batch-export]').forEach(b=>b.onclick=()=>action(async()=>{await workApi('batches.export',{id:b.dataset.batchExport});workState.tab='tasks';await renderWork()}));
  workPanel.querySelectorAll('[data-undo-batch]').forEach(b=>b.onclick=()=>action(async()=>{await workApi('batches.undo',{id:b.dataset.undoBatch});toast('批次已撤销');await renderWork()}));
}
async function workIssues(request){
  const result=await workApi('issues.list',{game:state.game,kind:workState.issueKind,page:workState.page,limit:24});if(request!==workState.request)return;
  if(result.status==='not_scanned'){
    $('workContent').innerHTML='<section class="panel"><h2>资料检查</h2><p>检查正文、版本、文件身份、译文和图片。扫描在后台进行，可继续浏览 MOD。</p><button id="workAudit">开始检查</button></section>';
    $('workAudit').onclick=()=>action(async()=>{await workApi('issues.audit',{game:state.game});workState.tab='tasks';await renderWork()});return;
  }
  $('workContent').innerHTML=`<section class="panel"><h2>资料待补充项</h2><p class="muted">当前范围：${esc(state.games.find(g=>g.id===state.game)?.title||'全部游戏')}。在左侧切换游戏。</p><div class="actions"><button id="workSelectPage">选择本页</button><button id="workIssueTask" class="primary">将已选项交给 AI</button></div>${result.items.length?result.items.map(i=>`<label class="work-issue"><input type="checkbox" data-issue="${esc(i.resourceId)}" ${workState.selected.has(i.resourceId)?'checked':''}><span><strong>${esc(i.name||i.resourceId)}</strong><span class="badge">${esc(ISSUE_NAMES[i.kind]||i.kind)}</span><small>${esc(i.evidence||i.reason||'需要核对来源')}</small></span></label>`).join(''):'<p>此范围没有发现待处理项。</p>'}${workPager(result.total)}</section>`;
  workPanel.querySelectorAll('[data-issue]').forEach(b=>b.onchange=()=>{b.checked?workState.selected.add(b.dataset.issue):workState.selected.delete(b.dataset.issue)});
  const auditButton=document.createElement('button');auditButton.textContent=result.stale?'资料已变化，重新检查':'重新检查';auditButton.onclick=()=>action(async()=>{await workApi('issues.audit',{game:state.game});workState.tab='tasks';await renderWork()});$('workContent').querySelector('.actions').append(auditButton);
  const filter=document.createElement('label');filter.innerHTML=`问题类型<select id="workIssueKind"><option value="">全部问题</option>${Object.entries(ISSUE_NAMES).map(([key,label])=>`<option value="${key}" ${key===workState.issueKind?'selected':''}>${label}</option>`).join('')}</select>`;$('workContent').querySelector('.actions').before(filter);$('workIssueKind').onchange=()=>action(async()=>{workState.issueKind=$('workIssueKind').value;workState.page=1;await renderWork()});
  $('workSelectPage').onclick=()=>{workPanel.querySelectorAll('[data-issue]').forEach(b=>{b.checked=true;workState.selected.add(b.dataset.issue)})};
  $('workIssueTask').onclick=()=>action(async()=>{if(!workState.selected.size){toast('请先选择需要整理的条目');return}await newWorkTask([...workState.selected])});bindWorkPager();
}
setInterval(async()=>{
  if(state.view!=='work'||workState.tab!=='tasks'||document.hidden||$('formDialog').open)return;
  const request=workState.request;
  try{
    const snapshot=await Promise.all([workApi('tasks.list',{page:workState.page,limit:24}),workApi('jobs.list',{limit:24})]);
    if(request!==workState.request||state.view!=='work'||workState.tab!=='tasks'||JSON.stringify(snapshot)===workState.signature)return;
    const active=document.activeElement;const id=active?.id;const dataset={...active?.dataset};
    await renderWork();
    if(id&&$(id))$(id).focus({preventScroll:true});else if(Object.keys(dataset).length){const target=[...workPanel.querySelectorAll('button')].find(b=>Object.entries(dataset).every(([k,v])=>b.dataset[k]===v));target?.focus({preventScroll:true})}
  }catch{/* Keep existing content visible during a temporary disconnection. */}
},5000);
async function workExchange(request){
  const artifacts=await workApi('artifacts.list',{limit:24});if(request!==workState.request)return;
  $('workContent').innerHTML=`<section class="panel"><h2>导入资料或译文</h2><p>支持新版资料包、资料修改 JSON/JSONL、Gemini 译文 JSONL。先检查差异，再提交。</p><label>文件内容<select id="workImportType"><option value="catalog">新增或更新资料包</option><option value="content">现有资料修改</option><option value="translations">翻译结果</option></select></label><label class="work-drop" id="workDrop">选择文件，或拖入此区域<input id="workImportFile" type="file" accept=".json,.jsonl"></label><label class="check"><input type="checkbox" id="workPartial">仅导入合格项（错误项会保留在结果中）</label><div id="workImportPreview"></div></section><section class="panel"><h2>导出与备份</h2><p>导出当前游戏的完整资料；在“全部游戏”下会导出全库。快照包含来源、文件、副本和已导入译文。</p><div class="actions"><button id="workExport">导出资料快照</button><button id="workBackup">备份工作资料</button></div></section><section class="panel"><h2>可下载成果</h2>${artifacts.items.length?artifacts.items.map(a=>`<div class="file-item"><a href="${esc(a.download)}" download>${esc(a.name)}</a><p class="muted">${bytes(a.bytes)} · ${new Date(a.created*1000).toLocaleString('zh-CN')}</p></div>`).join(''):'<p class="muted">暂无已登记成果。</p>'}</section>`;
  const readFile=async file=>{if(!file)return;$('workImportPreview').innerHTML='';workState.preview=null;if(file.size>30*1024*1024)throw new Error('请把导入文件拆分到每份 30 MiB 以内');const raw=await file.text();const kind=$('workImportType').value;let payload;
    if(kind==='translations')payload={content:raw};else if(kind==='catalog')payload={package:JSON.parse(raw)};else{let records;try{records=JSON.parse(raw)}catch{records=raw.split(/\r?\n/).filter(x=>x.trim()).map(x=>JSON.parse(x))}payload={records:Array.isArray(records)?records:records.records||[records]}}
    payload.allowPartial=$('workPartial').checked;const result=await workApi(kind+'.preview',payload);workState.preview=result;workState.previewOperation=kind;
    $('workImportPreview').innerHTML=`<p>合格 ${result.valid} 项，错误 ${result.errors.length} 项。${result.canApply?'可以提交。':'请修正错误或明确选择仅导入合格项，再重新选择文件。'}</p><details><summary>查看预览与错误</summary><pre>${esc(JSON.stringify(result,null,2))}</pre></details><div class="actions"><button id="workApply" class="primary" ${result.canApply?'':'disabled'}>提交本次预览</button><button id="workDownloadErrors">下载待修正项</button></div>`;
    $('workDownloadErrors').disabled=!result.errors.length;
    $('workDownloadErrors').onclick=()=>{let records=payload.records||payload.package?.records;if(!records){try{records=JSON.parse(raw)}catch{records=raw.split(/\r?\n/).filter(x=>x.trim()).map(x=>JSON.parse(x))}}const failed=result.errors.map(e=>records[e.index]).filter(x=>x!==undefined);downloadWorkJson(kind==='catalog'?{...payload.package,records:failed}:failed,'待修正资料.json')};
    $('workApply').onclick=()=>action(async()=>{const apply=await workApi(kind==='translations'?'translations.import':kind+'.apply',{previewId:result.previewId,commitMode:'batched'});toast(apply.status?'已加入分批队列':'资料已提交');workState.tab='tasks';await renderWork()});
  };
  $('workImportFile').onchange=e=>action(()=>readFile(e.target.files[0]));const drop=$('workDrop');drop.ondragover=e=>{e.preventDefault();drop.classList.add('dragging')};drop.ondragleave=()=>drop.classList.remove('dragging');drop.ondrop=e=>{e.preventDefault();drop.classList.remove('dragging');action(()=>readFile(e.dataTransfer.files[0]))};
  $('workExport').onclick=()=>action(async()=>{await workApi('catalog.export',{game:state.game});workState.tab='tasks';await renderWork()});
  $('workBackup').onclick=()=>action(async()=>{await workApi('maintenance.backup');workState.tab='tasks';await renderWork()});
}
