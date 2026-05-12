(() => {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;

  const backdropCloseEls = modal.querySelectorAll('[data-auth-close]');
  const openEls = document.querySelectorAll('[data-auth-open]');
  const tabs = Array.from(modal.querySelectorAll('[data-auth-tab]'));
  const titleEl = modal.querySelector('#auth-modal-title');
  const errorEl = modal.querySelector('[data-auth-error]');
  const forms = {
    login: modal.querySelector('[data-auth-form="login"]'),
    register: modal.querySelector('[data-auth-form="register"]'),
  };

  const showError = (msg) => {
    if (!errorEl) return;
    if (!msg) {
      errorEl.hidden = true;
      errorEl.textContent = '';
      return;
    }
    errorEl.hidden = false;
    errorEl.textContent = msg;
  };

  const setTab = (tab) => {
    const isLogin = tab === 'login';
    if (forms.login) forms.login.hidden = !isLogin;
    if (forms.register) forms.register.hidden = isLogin;
    tabs.forEach((t) => t.classList.toggle('auth-modal__tab--active', t.dataset.authTab === tab));
    if (titleEl) titleEl.textContent = isLogin ? 'Вхід' : 'Реєстрація';
    showError('');
    const focusEl = (isLogin ? forms.login : forms.register)?.querySelector('input[name="username"]');
    setTimeout(() => focusEl?.focus(), 0);
  };

  const open = () => {
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    setTab('login');
  };

  const close = () => {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    showError('');
  };

  openEls.forEach((el) => el.addEventListener('click', (e) => { e.preventDefault(); open(); }));
  backdropCloseEls.forEach((el) => el.addEventListener('click', close));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('open')) close();
  });

  tabs.forEach((t) => t.addEventListener('click', () => setTab(t.dataset.authTab)));

  const ajaxSubmit = async (form) => {
    showError('');
    const fd = new FormData(form);
    const res = await fetch(form.action, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: fd,
      credentials: 'same-origin',
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data && data.ok && data.redirect) {
      window.location.href = data.redirect;
      return;
    }
    const errors = (data && Array.isArray(data.errors) && data.errors.length) ? data.errors : ['Перевірте дані та спробуйте ще раз.'];
    showError(errors[0]);
  };

  Object.values(forms).forEach((form) => {
    if (!form) return;
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      ajaxSubmit(form);
    });
  });
})();

