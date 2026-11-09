// Interactions for the static VN Law Guard page: theme, mobile menu, tabs, demo console.
// No analytics, no cookies, no third-party requests.
(function () {
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  // Theme
  var themeBtn = $('#theme-toggle');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('vn-law-guard-theme', next); } catch (e) {}
  });

  // Mobile menu
  var menuBtn = $('#menu-toggle'), mobileNav = $('#mobile-nav');
  function setMenu(open) {
    if (!menuBtn || !mobileNav) return;
    mobileNav.hidden = !open;
    menuBtn.setAttribute('aria-expanded', String(open));
    menuBtn.setAttribute('aria-label', open ? 'Đóng menu' : 'Mở menu');
  }
  if (menuBtn) menuBtn.addEventListener('click', function () { setMenu(mobileNav.hidden); });
  $$('#mobile-nav a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });

  // Generic tabs: triggers carry data-<group> and aria-controls
  function bindTabs(attr) {
    var triggers = $$('[data-' + attr + ']');
    triggers.forEach(function (btn) {
      btn.addEventListener('click', function () {
        triggers.forEach(function (b) {
          var on = b === btn;
          b.dataset.state = on ? 'active' : 'inactive';
          b.setAttribute('aria-selected', String(on));
          var panel = document.getElementById(b.getAttribute('aria-controls'));
          if (panel) { panel.hidden = !on; panel.dataset.state = on ? 'active' : 'inactive'; }
        });
      });
    });
  }
  bindTabs('case');
  bindTabs('platform');

  // Demo console (illustrative data, same as the original design)
  var PHASES = {
    'first-visit': { title: 'Lần truy cập đầu tiên', status: 'ĐANG KIỂM TRA NETWORK', tone: 'signal', lines: [
      ['00:00.00', 'Mở trang chủ · phiên mới', 'console-foreground'],
      ['00:00.41', 'Đang theo dõi request bên thứ ba…', 'cyan'],
      ['00:01.08', 'Cookie trước consent: 0', 'signal'],
      ['00:01.12', 'Đang chờ lựa chọn của người dùng', 'console-muted']] },
    decline: { title: 'Sau khi từ chối', status: 'ĐÃ GHI NHẬN LỰA CHỌN', tone: 'warning', lines: [
      ['00:00.00', 'Người dùng chọn Từ chối', 'console-foreground'],
      ['00:00.24', 'GA4 · ping consent mode · gcs=G100', 'warning'],
      ['00:00.42', 'Cookie _ga · chưa được tạo', 'signal'],
      ['00:00.51', 'Cookie _fbp · chưa được tạo', 'signal']] },
    accept: { title: 'Sau khi đồng ý', status: 'ĐÃ GHI NHẬN LỰA CHỌN', tone: 'signal', lines: [
      ['00:00.00', 'Người dùng chọn Đồng ý', 'console-foreground'],
      ['00:00.31', 'GA4 · collect · gcs=G111', 'cyan'],
      ['00:00.46', 'Cookie _ga · được tạo sau consent', 'signal'],
      ['00:00.63', 'Meta Pixel · tải sau consent', 'signal']] }
  };
  var ACTIVE = 'border-cyan/35 bg-cyan/10 text-cyan hover:bg-cyan/15 hover:text-cyan';
  var IDLE = 'border-transparent text-console-muted hover:bg-console-active hover:text-console-foreground';
  var state = { phase: 'first-visit', viewport: 'desktop' };

  function swap(el, from, to) {
    from.split(' ').forEach(function (c) { el.classList.remove(c); });
    to.split(' ').forEach(function (c) { el.classList.add(c); });
  }

  function render() {
    var p = PHASES[state.phase], mobile = state.viewport === 'mobile';
    $$('[data-phase]').forEach(function (b) {
      var on = b.dataset.phase === state.phase;
      b.setAttribute('aria-pressed', String(on));
      swap(b, on ? IDLE : ACTIVE, on ? ACTIVE : IDLE);
      b.disabled = mobile && b.dataset.phase !== 'first-visit';
      b.title = b.disabled ? 'Phiên mobile chỉ đo trạng thái chưa chọn' : '';
    });
    $$('[data-viewport]').forEach(function (b) {
      var on = b.dataset.viewport === state.viewport;
      b.dataset.state = on ? 'active' : 'inactive';
      b.setAttribute('aria-selected', String(on));
    });
    $('#vp-size').textContent = mobile ? '390 × 844' : '1366 × 768';
    $('#vp-foot').textContent = mobile ? 'MOBILE 390PX' : 'DESKTOP 1366PX';
    $('#vp-phases').textContent = mobile ? 'Chromium · phiên chưa chọn' : 'Chromium · 3 phases';
    $('#phase-title').textContent = p.title;
    var status = $('#phase-status');
    status.textContent = p.status;
    status.className = 'shrink-0 font-mono text-[9px] text-' + p.tone;
    $('#vp-dot').className = 'size-1.5 rounded-full bg-' + p.tone;

    var box = $('#phase-lines');
    box.textContent = '';
    p.lines.forEach(function (l, i) {
      var row = document.createElement('div');
      row.className = 'flex items-start gap-2.5 animate-in fade-in-0 slide-in-from-bottom-1 duration-300';
      var time = document.createElement('span');
      time.className = 'shrink-0 text-console-muted';
      time.textContent = '[' + l[0] + ']';
      var text = document.createElement('span');
      text.className = 'min-w-0 break-words text-' + l[2];
      text.textContent = l[1];
      row.appendChild(time); row.appendChild(text);
      if (state.phase === 'first-visit' && i === p.lines.length - 1) {
        var dot = document.createElement('span');
        dot.className = 'mt-1 size-1.5 shrink-0 animate-pulse rounded-full bg-signal';
        row.appendChild(dot);
      }
      box.appendChild(row);
    });
  }

  $$('[data-phase]').forEach(function (b) {
    b.addEventListener('click', function () { state.phase = b.dataset.phase; render(); });
  });
  $$('[data-viewport]').forEach(function (b) {
    b.addEventListener('click', function () {
      state.viewport = b.dataset.viewport;
      if (state.viewport === 'mobile') state.phase = 'first-visit';
      render();
    });
  });
})();
