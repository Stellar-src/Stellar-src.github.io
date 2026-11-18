(() => {
  const colors = {linen:'#f2f1eb', glacier:'#eaf0f6', graphite:'#2e3440', white:'#ffffff'};
  const key = 'stellar-src-reading-palette';
  let palette = 'linen';
  try {
    const saved = localStorage.getItem(key);
    if (Object.hasOwn(colors, saved)) palette = saved;
    else if (localStorage.getItem('stellar-src-theme-v1') === 'dark') palette = 'graphite';
  } catch {}
  function apply(value) {
    document.documentElement.dataset.palette = value;
    document.querySelector('meta[name="theme-color"]').content = colors[value];
  }
  apply(palette);
  document.addEventListener('DOMContentLoaded', () => {
    const menu = document.querySelector('.palette');
    const journal = document.querySelector('#og-journal');
    if ('showPopover' in HTMLElement.prototype) {
      const tools = document.createElement('div');
      tools.popover = 'auto';
      tools.className = 'context-tools';
      tools.setAttribute('role','group');
      tools.setAttribute('aria-label','右键操作');
      journal.append(tools);
      journal.addEventListener('contextmenu', event => {
        if (event.button !== 2 || event.shiftKey || !matchMedia('(hover:hover) and (pointer:fine)').matches ||
            event.pointerType === 'touch' || event.target.closest('input,textarea,[contenteditable="true"]')) return;
        event.preventDefault();
        const selection = String(window.getSelection());
        const link = event.target.closest('a[href]');
        if (tools.matches(':popover-open')) tools.hidePopover();
        tools.replaceChildren();
        function action(text, run) {
          const button = document.createElement('button');
          button.type = 'button';
          button.textContent = text;
          button.addEventListener('click', () => { tools.hidePopover(); run(); });
          tools.append(button);
        }
        function copy(text) {
          try {
            navigator.clipboard.writeText(text).catch(() => window.prompt('复制以下内容', text));
          } catch { window.prompt('复制以下内容', text); }
        }
        if (link) {
          const open = document.createElement('a');
          open.href = link.href;
          open.target = '_blank';
          open.rel = 'noopener';
          open.textContent = '在新标签页打开';
          open.addEventListener('click', () => tools.hidePopover());
          tools.append(open);
          action('复制链接地址', () => copy(link.href));
        }
        if (selection) action('复制选中文字', () => copy(selection));
        action('复制本页网址', () => copy(location.href));
        action('刷新页面', () => location.reload());
        const hint = document.createElement('small');
        hint.textContent = 'Shift + 右键打开浏览器菜单';
        tools.append(hint);
        tools.showPopover();
        tools.style.left = Math.max(0, Math.min(event.clientX, innerWidth - tools.offsetWidth - 4))+'px';
        tools.style.top = Math.max(0, Math.min(event.clientY, innerHeight - tools.offsetHeight - 4))+'px';
        tools.firstElementChild.focus({preventScroll:true});
      });
    }
    menu.querySelector('input[value="'+palette+'"]').checked = true;
    menu.addEventListener('change', event => {
      const value = event.target.value;
      if (!Object.hasOwn(colors, value)) return;
      apply(value);
      try {localStorage.setItem(key,value)} catch {}
    });
    document.addEventListener('click', event => {
      if (!menu.contains(event.target)) menu.open = false;
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.open) {
        menu.open = false;
        menu.querySelector('summary').focus();
      }
    });
  });
})();
