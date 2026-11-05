'use strict';
// Interaction layer: direct manipulation, keyboard flow and visible feedback.
// It only drives existing view functions; it never writes data on its own.
(()=>{
const INTERACTIVE='a,button,input,select,textarea,label,summary,details,dialog,[contenteditable],[role="button"]';
const reduceMotion=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
const docked=matchMedia('(min-width:1700px)');
const hasSelection=()=>String(window.getSelection?.()||'').trim().length>0;
const inLibrary=view=>typeof isLibraryView==='function'?isLibraryView(view):['browse','favorites','recent'].includes(view);
const playOnce=(node,name)=>{if(!node||reduceMotion())return;node.classList.remove(name);void node.offsetWidth;node.classList.add(name);node.addEventListener('animationend',()=>node.classList.remove(name),{once:true})};
const remember=(key,value)=>{try{if(value===undefined)return localStorage.getItem(key);localStorage.setItem(key,value)}catch{return null}};

// Offsets for the detail panel and the phone drawer follow the real header height.
const header=document.querySelector('.topbar');
const syncTopbar=()=>document.documentElement.style.setProperty('--nx-topbar',header.offsetHeight+'px');
new ResizeObserver(syncTopbar).observe(header);syncTopbar();

// Page-level state as body classes (cheaper than body:has() selectors, which make the browser
// re-check page-wide styles on every DOM change).
const bodyFlag=(name,on)=>document.body.classList.toggle(name,Boolean(on));
const watchShown=(id,name)=>{const node=$(id);if(!node)return;const paint=()=>bodyFlag(name,!node.hidden);new MutationObserver(paint).observe(node,{attributes:true,attributeFilter:['hidden']});paint()};
watchShown('jobTray','has-job-tray');watchShown('quickActionNotice','has-notice');watchShown('compareTray','has-compare-tray');
new MutationObserver(()=>bodyFlag('menu-open',$('sidebar').classList.contains('open'))).observe($('sidebar'),{attributes:true,attributeFilter:['class']});
const paintDialogs=()=>bodyFlag('has-dialog',document.querySelector('dialog[open]'));
for(const dialog of document.querySelectorAll('dialog'))new MutationObserver(paintDialogs).observe(dialog,{attributes:true,attributeFilter:['open']});

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
  $('detail').dataset.step=delta>0?'next':'prev';
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
  let signature='',toggledAt=0,justToggled='';
  const paintCategories=()=>{
    const options=[...category.options].filter(option=>option.value);
    const next=options.map(option=>option.value+'\u0000'+option.textContent).join('\u0001');
    if(next!==signature){
      signature=next;
      list.innerHTML=options.map(option=>{const match=option.textContent.match(/^(.*) \((\d+)\)$/);return `<button type="button" class="facet" data-value="${esc(option.value)}" aria-pressed="false"><span class="facet-box" aria-hidden="true"></span><span class="facet-name">${esc(match?match[1]:option.textContent)}</span>${match?`<span class="facet-count">(${match[2]})</span>`:''}</button>`}).join('')||'<p class="muted">暂无用途分类</p>';
    }
    list.querySelectorAll('.facet').forEach(button=>button.setAttribute('aria-pressed',String(category.value===button.dataset.value)));
    if(justToggled&&Date.now()-toggledAt<600){const button=list.querySelector(`.facet[data-value="${CSS.escape(justToggled)}"]`);if(button&&!button.classList.contains('just-toggled'))playOnce(button,'just-toggled')}
  };
  list.addEventListener('click',event=>{const button=event.target.closest('.facet');if(!button)return;justToggled=button.dataset.value;toggledAt=Date.now();category.value=category.value===button.dataset.value?'':button.dataset.value;category.dispatchEvent(new Event('change',{bubbles:true}))});
  new MutationObserver(paintCategories).observe(category,{childList:true});
  category.addEventListener('change',paintCategories);paintCategories();
}
// Library breadcrumb, like "Home › Elden Ring › Mods": the hidden eyebrow line becomes
// 资料库 › <current page title>, kept in step with the title app.js writes.
const pageTitle=$('pageTitle'),crumb=document.querySelector('#browseView .heading .eyebrow');
if(pageTitle&&crumb){
  crumb.classList.add('crumbs');crumb.setAttribute('aria-hidden','true');
  const paintCrumb=()=>{crumb.innerHTML=`<span>资料库</span><span class="crumb-sep">›</span><span>${esc(pageTitle.textContent||'')}</span>`};
  new MutationObserver(paintCrumb).observe(pageTitle,{childList:true,characterData:true,subtree:true});paintCrumb();
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

// Header game chip, like Nexus' "[game] ×" context switch: shows the current game, opens a
// menu of games, × returns to all games. It drives the same changeGame() as the game buttons.
const brand=document.querySelector('.topbar .brand'),gameButtons=$('games');
if(brand&&gameButtons){
  const chip=document.createElement('div');chip.className='game-chip';
  chip.innerHTML=`<button type="button" class="game-chip-main" aria-haspopup="menu" aria-expanded="false"><span class="game-chip-thumb" aria-hidden="true"></span><span class="game-chip-name">全部游戏</span><svg class="icon" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m4.5 6.5 3.5 3.5 3.5-3.5"/></svg></button><button type="button" class="game-chip-clear" aria-label="查看全部游戏" title="查看全部游戏" hidden>×</button><div class="game-chip-menu" role="menu" aria-label="切换游戏" hidden></div>`;
  brand.after(chip);
  const main=chip.querySelector('.game-chip-main'),clear=chip.querySelector('.game-chip-clear'),menu=chip.querySelector('.game-chip-menu');
  let closing=null;
  const setOpen=open=>{clearTimeout(closing);main.setAttribute('aria-expanded',String(open));if(open){menu.classList.remove('is-closing');menu.hidden=false;menu.querySelector('[aria-checked="true"]')?.focus();return}if(menu.hidden)return;if(reduceMotion()){menu.hidden=true;return}menu.classList.add('is-closing');closing=setTimeout(()=>{menu.hidden=true;menu.classList.remove('is-closing')},120)};
  const paintChip=()=>{
    const games=state.games||[],current=games.find(game=>game.id===state.game),total=games.reduce((sum,game)=>sum+(game.count||0),0);
    const name=current?current.title:'全部游戏';
    chip.querySelector('.game-chip-name').textContent=name;chip.querySelector('.game-chip-thumb').textContent=[...name][0]||'';
    clear.hidden=!current;chip.classList.toggle('has-game',Boolean(current));
    menu.innerHTML=[{id:'',title:'全部游戏',count:total},...games].map(game=>`<button type="button" role="menuitemradio" aria-checked="${game.id===(state.game||'')}" data-game-pick="${esc(game.id)}"><span>${esc(game.title)}</span><small>${number(game.count||0)}</small></button>`).join('');
  };
  main.onclick=()=>setOpen(menu.hidden);
  clear.onclick=()=>action(()=>changeGame(''));
  menu.addEventListener('click',event=>{const pick=event.target.closest('[data-game-pick]');if(!pick)return;setOpen(false);action(()=>changeGame(pick.dataset.gamePick))});
  menu.addEventListener('keydown',event=>{if(event.key==='Escape'){event.stopPropagation();setOpen(false);main.focus()}});
  document.addEventListener('click',event=>{if(!menu.hidden&&!chip.contains(event.target))setOpen(false)});
  new MutationObserver(paintChip).observe(gameButtons,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});paintChip();
}
// Library hero, like the top of a Nexus mods page: art from the first local cover, breadcrumb,
// cover tile + title, the game buttons as quick switches and the scope tabs at its foot.
const heroView=$('browseView'),heroTitle=$('pageTitle');
if(heroView&&heroTitle&&gameButtons){
  const hero=document.createElement('section');hero.className='library-hero';hero.setAttribute('aria-label','资料库');
  const crumbs=heroView.querySelector('.heading .eyebrow'),scope=heroView.querySelector(':scope>.ui-subnav');
  const head=document.createElement('div');head.className='library-hero-head';
  const tile=document.createElement('div');tile.className='library-hero-tile';tile.setAttribute('aria-hidden','true');
  const titles=document.createElement('div');titles.className='library-hero-titles';titles.append(heroTitle);
  head.append(tile,titles);
  const label=gameButtons.previousElementSibling;if(label?.classList.contains('section-label'))label.hidden=true;
  gameButtons.classList.add('library-games');gameButtons.setAttribute('role','group');gameButtons.setAttribute('aria-label','切换游戏');
  if(crumbs)hero.append(crumbs);hero.append(head,gameButtons);if(scope)hero.append(scope);
  heroView.prepend(hero);
  const paintArt=()=>{const img=[...document.querySelectorAll('#cards .card .cover img')].find(image=>image.complete&&image.naturalWidth>0);const src=img?.getAttribute('src');hero.classList.toggle('has-art',Boolean(src));if(src){const value=`url("${src.replace(/["\\\n\r]/g,encodeURIComponent)}")`;hero.style.setProperty('--hero-art',value)}else hero.style.removeProperty('--hero-art');tile.textContent=src?'':([...(heroTitle.textContent||'')][0]||'')};
  new MutationObserver(paintArt).observe($('cards'),{childList:true});
  // only images that actually loaded are reused, so a broken cover is never fetched twice
  $('cards').addEventListener('load',event=>{if(event.target.matches?.('.cover img')&&!hero.classList.contains('has-art'))paintArt()},true);
  new MutationObserver(paintArt).observe(heroTitle,{childList:true,characterData:true,subtree:true});paintArt();
}
// Connection status as a small dot (text kept for screen readers and as tooltip).
const connection=$('connection');
if(connection){const paintConnection=()=>{const text=connection.textContent||'';connection.title=text;connection.classList.toggle('is-offline',/中断|失败|重试/.test(text))};new MutationObserver(paintConnection).observe(connection,{childList:true,characterData:true,subtree:true});paintConnection()}

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

// Micro-interactions: small, quick responses to small actions (all skipped with reduced motion).
// favourite: a short pop where the press happened
document.addEventListener('click',event=>{const star=event.target.closest?.('[data-action="favorite"],#detailFavorite');if(star)playOnce(star,'is-popping')},true);
// results: new tiles fade in, slightly staggered, whenever the list is replaced
// (cards are fresh elements here, so no forced reflow is needed to start the animation)
new MutationObserver(records=>{if(reduceMotion())return;let index=0;for(const record of records)for(const card of record.addedNodes){if(card.nodeType!==1||!card.classList.contains('card'))continue;card.style.setProperty('--enter-delay',Math.min(index++,12)*22+'ms');card.classList.add('is-entering');card.addEventListener('animationend',()=>card.classList.remove('is-entering'),{once:true})}}).observe($('cards'),{childList:true});
// prev / next: the new MOD slides in from the side it came from
new MutationObserver(()=>{const detail=$('detail'),step=detail.dataset.step;if(!step)return;delete detail.dataset.step;for(const node of [detail.querySelector('.detail-masthead'),$('detailBody')])playOnce(node,step==='next'?'step-from-right':'step-from-left')}).observe($('detailHeading'),{childList:true});
// closing the panel: a plain panel shape slides away (no copied content, so nothing is duplicated)
new MutationObserver(records=>{const detail=$('detail');if(!detail.hidden||reduceMotion()||!records.some(record=>record.oldValue===null))return;const box=detail.getBoundingClientRect();if(!box.width&&!records.length)return;const ghost=document.createElement('div');ghost.className='detail-ghost';ghost.setAttribute('aria-hidden','true');const mast=detail.querySelector('.detail-masthead');ghost.style.setProperty('--ghost-head',(mast?.offsetHeight||0)+'px');document.body.append(ghost);ghost.addEventListener('animationend',()=>ghost.remove(),{once:true});setTimeout(()=>ghost.remove(),400)}).observe($('detail'),{attributes:true,attributeFilter:['hidden'],attributeOldValue:true});
// header picks up a shadow once the page scrolls under it
const topbar=document.querySelector('.topbar');const paintScrolled=()=>topbar?.classList.toggle('is-scrolled',window.scrollY>4);window.addEventListener('scroll',paintScrolled,{passive:true});paintScrolled();
})();
