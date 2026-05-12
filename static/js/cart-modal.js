/**
 * Cart modal: open on "buy", inline +/- updates via AJAX.
 */
(function () {
  function qs(sel) {
    return document.querySelector(sel);
  }

  function getCsrf() {
    var panel = qs('#ai-panel');
    if (panel && panel.dataset && panel.dataset.csrf) return panel.dataset.csrf;
    return '';
  }

  function ensureModal() {
    return qs('#cart-modal');
  }

  function openModal() {
    var m = ensureModal();
    if (!m) return;
    m.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    var m = ensureModal();
    if (!m) return;
    m.classList.remove('open');
    document.body.style.overflow = '';
  }

  async function refreshModal() {
    var m = ensureModal();
    if (!m) return;
    var url = m.getAttribute('data-fragment-url');
    if (!url) return;
    var resp = await fetch(url, { credentials: 'same-origin' });
    var data = await resp.json();
    var body = qs('#cart-modal-body');
    if (body) body.innerHTML = data.html || '';
    var cnt = qs('[data-cart-count]');
    if (cnt) cnt.textContent = data.cart_count ? String(data.cart_count) : '';
    wireModalActions();
  }

  function updateNavbarCount(count) {
    var el = qs('[data-navbar-cart]');
    if (!el) return;
    if (!count) {
      el.textContent = 'Кошик';
    } else {
      el.textContent = 'Кошик (' + count + ')';
    }
  }

  async function post(url, formData) {
    var resp = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': getCsrf(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: formData,
    });
    return await resp.json();
  }

  async function addAndOpen(productId, qty) {
    var m = ensureModal();
    if (!m) return;
    var addUrlTpl = m.getAttribute('data-add-url-template');
    if (!addUrlTpl) return;
    var url = addUrlTpl.replace(/0\/?$/, String(productId) + '/');
    var fd = new FormData();
    fd.set('qty', String(qty || 1));
    var data = await post(url, fd);
    var body = qs('#cart-modal-body');
    if (body) body.innerHTML = data.html || '';
    updateNavbarCount(data.cart_count || 0);
    openModal();
    wireModalActions();
  }

  async function setQty(productId, qty) {
    var m = ensureModal();
    var urlTpl = m.getAttribute('data-update-url-template');
    var url = urlTpl.replace(/0\/?$/, String(productId) + '/');
    var fd = new FormData();
    fd.set('qty', String(qty));
    var data = await post(url, fd);
    var body = qs('#cart-modal-body');
    if (body) body.innerHTML = data.html || '';
    updateNavbarCount(data.cart_count || 0);
    wireModalActions();
  }

  async function remove(productId) {
    var m = ensureModal();
    var urlTpl = m.getAttribute('data-remove-url-template');
    var url = urlTpl.replace(/0\/?$/, String(productId) + '/');
    var fd = new FormData();
    var data = await post(url, fd);
    var body = qs('#cart-modal-body');
    if (body) body.innerHTML = data.html || '';
    updateNavbarCount(data.cart_count || 0);
    wireModalActions();
  }

  function wireModalActions() {
    var root = qs('#cart-modal-body');
    if (!root) return;

    root.querySelectorAll('[data-cart-close]').forEach(function (b) {
      b.addEventListener('click', closeModal, { once: true });
    });

    root.querySelectorAll('[data-cart-inc]').forEach(function (b) {
      b.addEventListener(
        'click',
        function () {
          var pid = parseInt(b.getAttribute('data-product-id'), 10);
          var row = b.closest('[data-cart-row]');
          var q = row ? row.querySelector('[data-cart-qty]') : null;
          var cur = q ? parseInt(q.textContent || '1', 10) : 1;
          setQty(pid, cur + 1);
        },
        { once: true }
      );
    });

    root.querySelectorAll('[data-cart-dec]').forEach(function (b) {
      b.addEventListener(
        'click',
        function () {
          var pid = parseInt(b.getAttribute('data-product-id'), 10);
          var row = b.closest('[data-cart-row]');
          var q = row ? row.querySelector('[data-cart-qty]') : null;
          var cur = q ? parseInt(q.textContent || '1', 10) : 1;
          var next = Math.max(1, cur - 1);
          setQty(pid, next);
        },
        { once: true }
      );
    });

    root.querySelectorAll('[data-cart-remove]').forEach(function (b) {
      b.addEventListener(
        'click',
        function () {
          var pid = parseInt(b.getAttribute('data-product-id'), 10);
          remove(pid);
        },
        { once: true }
      );
    });
  }

  document.addEventListener('click', function (e) {
    var buy = e.target && e.target.closest && e.target.closest('[data-cart-buy]');
    if (!buy) return;
    e.preventDefault();
    var pid = parseInt(buy.getAttribute('data-product-id'), 10);
    if (!pid) return;
    addAndOpen(pid, 1);
  });

  document.addEventListener('click', function (e) {
    var open = e.target && e.target.closest && e.target.closest('[data-cart-open]');
    if (!open) return;
    var m = ensureModal();
    if (!m) return;
    e.preventDefault();
    openModal();
    refreshModal();
  });

  document.addEventListener('click', function (e) {
    var backdrop = e.target && e.target.closest && e.target.closest('[data-cart-backdrop]');
    if (!backdrop) return;
    closeModal();
  });

  window.cartModalClose = closeModal;
})();

