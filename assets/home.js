
(() => {
 const root = document.getElementById('og-journal');
 const cover = root.querySelector('.cover');
 const finder = root.querySelector('.finder');
 const symbol = root.querySelector('.reticle');
 const reduced = matchMedia('(prefers-reduced-motion: reduce)');
 const fine = matchMedia('(hover:hover) and (pointer:fine)');
 const fullColor = root.querySelector('.switch');
 let locked = false, pressing = false, moving = false, frame = 0;
 let targetX = 0, targetY = 0, lensX = 0, lensY = 0, radius = 0, mode = 'inspect';
 let firstPaint=true;
 function paint() {
   frame = 0;
   const goal = locked ? Math.hypot(cover.offsetWidth, cover.offsetHeight)+2 : !moving || mode === 'link' ? 0 : pressing ? 156 : 74;
   const delta = reduced.matches ? 1 : .25;
   if (firstPaint && locked) radius=goal;
   firstPaint=false;
   lensX += (targetX-lensX)*.55; lensY += (targetY-lensY)*.55;
   radius += (goal-radius)*delta;
   cover.style.setProperty('--px',lensX+'px');cover.style.setProperty('--py',lensY+'px');cover.style.setProperty('--rad',radius+'px');
   if(Math.abs(radius-goal)>.3 || Math.abs(targetX-lensX)+Math.abs(targetY-lensY)>.4) schedule();
 }
 paint();
 new ResizeObserver(schedule).observe(cover);
 function schedule(){if(!frame)frame=requestAnimationFrame(paint)}
 function position(event){
   const rect=cover.getBoundingClientRect();
   targetX=event.clientX-rect.left;targetY=event.clientY-rect.top;
   if(!moving){lensX=targetX;lensY=targetY}
   moving=true;
   mode=event.target.closest('button,a')?'link':pressing?'press':'inspect';
   cover.dataset.mode=mode;
   symbol.textContent=mode==='link'?'↗':'+';
   finder.style.transform='translate('+targetX+'px,'+targetY+'px)';
   cover.classList.toggle('tracking',event.pointerType==='mouse' && fine.matches && !reduced.matches);
   schedule();
 }
 function reset(){pressing=false;moving=false;cover.classList.remove('tracking');schedule()}
 cover.addEventListener('pointermove',event=>{if(event.pointerType==='mouse' && !reduced.matches || pressing)position(event)});
 cover.addEventListener('pointerdown',event=>{
   if(event.button!==0 || event.target.closest('button,a'))return;
   pressing=true;position(event);
 });
 window.addEventListener('pointerup',event=>{if(!pressing)return;pressing=false;if(event.pointerType==='mouse' && cover.contains(event.target))position(event);else reset()});
 cover.addEventListener('pointerleave',reset);cover.addEventListener('pointercancel',reset);
 window.addEventListener('blur',reset);reduced.addEventListener('change',reset);
 root.addEventListener('keydown',event=>{if(event.key==='Tab')reset()});
 fullColor.addEventListener('click',()=>{locked=!locked;fullColor.setAttribute('aria-pressed',String(locked));schedule()});
 root.querySelectorAll('[data-index]').forEach(button=>button.addEventListener('click',()=>{
    const notes=root.querySelector('#og-notes');notes.scrollIntoView({behavior:reduced.matches?'instant':'smooth',block:'start'});notes.querySelector('.entry')?.focus({preventScroll:true});
 }));
})();
(() => {
  const journal = document.getElementById('og-journal');
  const toggle = journal.querySelector('.theme-button');
  const label = toggle.querySelector('.theme-label');
  const key = 'stellar-src-theme-v1';
  function setTheme(theme) {
    journal.dataset.theme = theme;
    const dark = theme === 'dark';
    label.textContent = dark ? 'Light Mode' : 'Dark Mode';
    toggle.setAttribute('aria-label', dark ? 'Light Mode，切换到浅色模式' : 'Dark Mode，切换到深色模式');


    const meta = document.querySelector('meta[name="og-standalone"]');
    if (meta) {
      document.documentElement.dataset.theme = theme;
      document.querySelector('meta[name="theme-color"]').content = dark ? '#202834' : '#f2f1eb';
    }
  }
  let initial = 'light';
  try { if (localStorage.getItem(key) === 'dark') initial = 'dark'; } catch {}
  setTheme(initial);
  toggle.addEventListener('click', () => {
    const next = journal.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    try { localStorage.setItem(key, next); } catch {}
  });
})();

function openLinkedNote() {
  const legacy = {'#read-fjord':'forest', '#read-cursor':'viewfinder'};
  const slug = legacy[location.hash];
  if (slug) location.replace('posts/' + slug + '/index.html');
}
openLinkedNote();
window.addEventListener('hashchange', openLinkedNote);
