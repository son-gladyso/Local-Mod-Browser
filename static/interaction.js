'use strict';
// Interaction layer: direct manipulation, keyboard flow and visible feedback.
// It only drives existing view functions; it never writes data on its own.
(()=>{
const INTERACTIVE='a,button,input,select,textarea,label,summary,details,dialog,[contenteditable],[role="button"]';
const reduceMotion=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
const docked=matchMedia('(min-width:1700px)');
const hasSelection=()=>String(window.getSelection?.()||'').trim().length>0;
const inLibrary=view=>typeof isLibraryView==='function'?isLibraryView(view):['browse','favorites','recent'].includes(view);
const remember=(key,value)=>{try{if(value===undefined)return localStorage.getItem(key);localStorage.setItem(key,value)}catch{return null}};

// Offsets for the detail panel and the phone drawer follow the real header height.
const header=document.querySelector('.topbar');
const syncTopbar=()=>document.documentElement.style.setProperty('--nx-topbar',header.offsetHeight+'px');
new ResizeObserver(syncTopbar).observe(header);syncTopbar();

// Narrow navigation drawer: a tap outside closes it without also activating what is underneath.
document.addEventListener('click',event=>{
  const sidebar=$('sidebar');
  if(!sidebar.classList.contains('open')||event.target.closest('#sidebar,#navToggle'))return;
  event.preventDefault();event.stopImmediatePropagation();
  sidebar.classList.remove('open');$('navToggle').focus({preventScroll:true});
},true);
new MutationObserver(()=>$('navToggle').setAttribute('aria-expanded',String($('sidebar').classList.contains('open')))).observe($('sidebar'),{attributes:true,attributeFilter:['class']});
$('navToggle').setAttribute('aria-expanded','false');$('navToggle').setAttribute('aria-controls','sidebar');

// Buttons that start async work show progress and ignore repeat presses until it settles.
let pressed=null;
document.addEventListener('click',event=>{
  const button=event.target.closest?.('button');
  if(!button)return;
  if(button.dataset.busy==='1'){event.preventDefault();event.stopImmediatePropagation();return}
  pressed=button;setTimeout(()=>{if(pressed===button)pressed=null},0);
},true);
const baseAction=window.action;
window.action=async function(fn){
  const button=pressed;pressed=null;
  if(!button||button.dataset.busy==='1')return baseAction(fn);
  button.dataset.busy='1';
  const timer=setTimeout(()=>{if(button.isConnected)button.setAttribute('aria-busy','true')},160);
  try{return await baseAction(fn)}
  finally{clearTimeout(timer);delete button.dataset.busy;button.removeAttribute('aria-busy')}
};

// The whole card is the target for "show me this MOD"; inner buttons, tags and links keep their own jobs.
$('cards').addEventListener('click',event=>{
  if(event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  const card=event.target.closest('.card[data-id]');
  if(!card||event.target.closest(INTERACTIVE)||hasSelection())return;
  card.querySelector('.card-title')?.focus({preventScroll:true});
  action(()=>openDetail(card.dataset.id,'overview'));
});

// Detail context: highlight the open card and step through the current result page.
const cardList=()=>[...document.querySelectorAll('#cards .card[data-id]')];
function syncDetailContext(){
  const id=state.detail?.id||'',open=Boolean(id)&&!$('detail').hidden&&inLibrary(state.view);
  const cards=cardList(),ids=cards.map(card=>card.dataset.id),index=open?ids.indexOf(id):-1;
  for(const card of cards){const active=open&&card.dataset.id===id;card.classList.toggle('is-active',active);if(active)card.setAttribute('aria-current','true');else card.removeAttribute('aria-current')}
  const step=document.querySelector('.detail-step');
  step.hidden=index<0||ids.length<2;
  $('detailPrev').disabled=index<=0;$('detailNext').disabled=index<0||index>=ids.length-1;
  $('detailPosition').textContent=index<0?'':`${index+1} / ${ids.length}`;
  $('detailPosition').title=index<0?'':`本页第 ${index+1} 个，共 ${ids.length} 个`;
}
async function stepDetail(delta,trigger){
  const ids=cardList().map(card=>card.dataset.id),index=ids.indexOf(state.detail?.id),target=ids[index+delta];
  if(index<0||!target)return;
  await openDetail(target,state.tab);
  if(state.detail?.id!==target)return;
  const card=document.querySelector(`#cards .card[data-id="${CSS.escape(target)}"]`);
  if(card){state.returnFocus=card.querySelector('.card-title')||state.returnFocus;card.scrollIntoView({block:'nearest',behavior:reduceMotion()?'auto':'smooth'})}
  if(trigger?.isConnected&&!trigger.disabled)trigger.focus({preventScroll:true});
}
$('detailPrev').onclick=()=>action(()=>stepDetail(-1,$('detailPrev')));
$('detailNext').onclick=()=>action(()=>stepDetail(1,$('detailNext')));
document.addEventListener('keydown',event=>{
  if(!['ArrowLeft','ArrowRight'].includes(event.key)||event.defaultPrevented||event.isComposing||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
  if(!state.detail||$('detail').hidden||document.querySelector('dialog[open]'))return;
  if(event.target.closest?.('input,textarea,select,[contenteditable]'))return;
  const button=$(event.key==='ArrowLeft'?'detailPrev':'detailNext');
  if(button.disabled||button.closest('[hidden]'))return;
  event.preventDefault();button.click();
});
// Tab counts, like "FILES 4": image records and files of the open MOD.
function syncTabCounts(){
  const m=state.detail;
  for(const [tab,count] of [['images',m?.imageCount],['files',m?.files?.length??m?.fileCount]]){
    const button=document.querySelector(`#detailTabs [data-tab="${tab}"]`);if(!button)continue;
    let label=button.querySelector('.tab-count');
    if(!m||count==null){label?.remove();continue}
    if(!label){label=document.createElement('span');label.className='tab-count';button.append(label)}
    label.textContent=String(count);
  }
}
// Hero banner from the MOD's first local image. Applied through CSSOM because the
// page's Content-Security-Policy (rightly) refuses inline style attributes.
function syncHero(){
  const mast=document.querySelector('#detail .detail-masthead'),hero=$('detailHeading').querySelector('.detail-hero[data-hero]');
  if(!mast)return;
  mast.classList.toggle('has-cover',Boolean(hero));
  if(hero)mast.style.setProperty('--hero',`url("${hero.dataset.hero.replace(/["\\\n\r]/g,encodeURIComponent)}")`);
  else mast.style.removeProperty('--hero');
}
new MutationObserver(()=>{syncTabCounts();syncHero()}).observe($('detailHeading'),{childList:true});
const contextObserver=new MutationObserver(syncDetailContext);
contextObserver.observe($('cards'),{childList:true});
contextObserver.observe($('detail'),{attributes:true,attributeFilter:['hidden']});
contextObserver.observe($('detailHeading'),{childList:true});

// When the panel floats over the list, a click on empty page space puts it away.
$('main').addEventListener('click',event=>{
  if(docked.matches||!state.detail||$('detail').hidden||event.defaultPrevented)return;
  if(event.target.closest(INTERACTIVE+',.card')||hasSelection())return;
  closeDetail();
});

// Undo notice (when the build has one) behaves like a snackbar: visible where the person is, then gets out of the way.
const notice=$('quickActionNotice'),LIFE=10000;
if(notice){let hideTimer=null,deadline=0,remaining=LIFE;
function sticky(){return $('quickUndo').disabled}
function startLife(duration){clearTimeout(hideTimer);if(notice.hidden||sticky())return;remaining=duration;deadline=Date.now()+duration;hideTimer=setTimeout(()=>{if(!notice.hidden&&!sticky()&&!notice.matches(':hover')&&!notice.contains(document.activeElement))notice.hidden=true},duration)}
function pauseLife(){if(!hideTimer)return;clearTimeout(hideTimer);hideTimer=null;remaining=Math.max(1500,deadline-Date.now())}
function restartNotice(){
  notice.classList.toggle('is-sticky',sticky());
  if(notice.hidden){clearTimeout(hideTimer);hideTimer=null;return}
  notice.style.setProperty('--life',LIFE+'ms');notice.classList.remove('is-fresh');void notice.offsetWidth;notice.classList.add('is-fresh');
  if(notice.matches(':hover')||notice.contains(document.activeElement)){remaining=LIFE;return}
  startLife(LIFE);
}
new MutationObserver(restartNotice).observe(notice,{attributes:true,attributeFilter:['hidden']});
new MutationObserver(restartNotice).observe($('quickActionMessage'),{childList:true,characterData:true,subtree:true});
new MutationObserver(()=>notice.classList.toggle('is-sticky',sticky())).observe($('quickUndo'),{attributes:true,attributeFilter:['disabled']});
notice.addEventListener('mouseenter',pauseLife);notice.addEventListener('focusin',pauseLife);
notice.addEventListener('mouseleave',()=>{if(!notice.contains(document.activeElement))startLife(remaining)});
notice.addEventListener('focusout',event=>{if(!notice.contains(event.relatedTarget)&&!notice.matches(':hover'))startLife(remaining)});
}

// Toasts can be dismissed with a click.
$('toast').title='点击关闭';$('toast').addEventListener('click',()=>{$('toast').hidden=true});

// Advanced filters stay folded until needed; the toggle shows how many are in effect.
const ADVANCED=['adult','updatedFrom','updatedTo','variants','localImages'];
let advancedCount=0;
function setAdvanced(open,save=true){$('advancedFilters').hidden=!open;$('moreFilters').setAttribute('aria-expanded',String(open));if(save)remember('mod-browser-more-filters',open?'1':'0');paintAdvanced()}
function paintAdvanced(){const count=ADVANCED.filter(key=>state.filters[key]).length,open=!$('advancedFilters').hidden;$('moreFilters').textContent=(open?'收起更多条件':'更多条件')+(count?` · ${count}`:'');if(count>advancedCount&&!open)setAdvanced(true,false);advancedCount=count}
$('moreFilters').onclick=()=>setAdvanced($('advancedFilters').hidden);
new MutationObserver(paintAdvanced).observe($('chips'),{childList:true});
setAdvanced(remember('mod-browser-more-filters')==='1',false);

// Library filter column (Nexus listing style): the 用途 select is mirrored as a checkbox
// list with counts. The select stays the single source of truth for app.js and tests.
const category=$('category');
if(category){
  const list=document.createElement('div');list.id='categoryList';list.className='facet-list';list.setAttribute('role','group');list.setAttribute('aria-label','用途');
  const label=category.closest('label');label.classList.add('has-facet-list');label.after(list);
  const paintCategories=()=>{
    const options=[...category.options].filter(option=>option.value);
    list.innerHTML=options.map(option=>{const match=option.textContent.match(/^(.*) \((\d+)\)$/);return `<button type="button" class="facet" data-value="${esc(option.value)}" aria-pressed="${category.value===option.value}"><span class="facet-box" aria-hidden="true"></span><span class="facet-name">${esc(match?match[1]:option.textContent)}</span>${match?`<span class="facet-count">(${match[2]})</span>`:''}</button>`}).join('')||'<p class="muted">暂无用途分类</p>';
  };
  list.addEventListener('click',event=>{const button=event.target.closest('.facet');if(!button)return;category.value=category.value===button.dataset.value?'':button.dataset.value;category.dispatchEvent(new Event('change',{bubbles:true}))});
  new MutationObserver(paintCategories).observe(category,{childList:true});
  category.addEventListener('change',paintCategories);paintCategories();
}
// Desktop "隐藏筛选" toggle above the filter column; phones keep the existing 展开筛选 button.
const browseView=$('browseView'),filtersPanel=$('filtersPanel');
if(browseView&&filtersPanel){
  const hide=document.createElement('button');Object.assign(hide,{type:'button',id:'hideFilters',className:'hide-filters'});
  hide.setAttribute('aria-controls','filtersPanel');filtersPanel.before(hide);
  const setHidden=(hidden,save=true)=>{browseView.classList.toggle('filters-hidden',hidden);hide.setAttribute('aria-expanded',String(!hidden));hide.innerHTML=`<svg class="icon" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M2.5 4.5h11M4.5 8h7M6.5 11.5h3"/></svg>${hidden?'显示筛选':'隐藏筛选'}`;if(save)remember('mod-browser-hide-filters',hidden?'1':'0')};
  hide.onclick=()=>setHidden(!browseView.classList.contains('filters-hidden'));
  setHidden(remember('mod-browser-hide-filters')==='1',false);
}

// Profiles: the whole card opens it, the open one is marked, empty states point to the next step.
$('profilesView').addEventListener('click',event=>{
  const card=event.target.closest('.profile-card');
  if(!card||event.target.closest(INTERACTIVE)||hasSelection())return;
  card.querySelector('[data-profile]')?.click();
});
new MutationObserver(()=>{const id=$('profileDetail')?.querySelector('[data-profile-id]')?.dataset.profileId||'';$('profilesView').querySelectorAll('.profile-card').forEach(card=>{const active=Boolean(id)&&card.querySelector('[data-profile]')?.dataset.profile===id;card.classList.toggle('is-active',active);if(active)card.setAttribute('aria-current','true');else card.removeAttribute('aria-current')})}).observe($('profilesView'),{childList:true,subtree:true});
document.addEventListener('click',event=>{
  const go=event.target.closest('[data-go-browse]');
  if(!go)return;
  event.preventDefault();
  action(async()=>{state.page=1;await setView('browse');$('main').focus({preventScroll:true})});
});

// Back to top for long result pages.
const toTop=document.createElement('button');
Object.assign(toTop,{id:'backToTop',type:'button',className:'back-to-top',textContent:'↑',title:'回到顶部',hidden:true});
toTop.setAttribute('aria-label','回到顶部');
document.body.append(toTop);
const paintTop=()=>{toTop.hidden=window.scrollY<900};
window.addEventListener('scroll',paintTop,{passive:true});paintTop();
toTop.onclick=()=>{window.scrollTo({top:0,behavior:reduceMotion()?'auto':'smooth'});$('main').focus({preventScroll:true})};
})();
