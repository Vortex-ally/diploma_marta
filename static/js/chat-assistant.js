/**
 * VeloUkraine — AI-чат: UI, localStorage, debounce, динамічні чіпси.
 * Логіка відокремлена від шаблону; використовує fetch + async/await.
 */
(function () {
  const STORAGE_KEY = 'veloukraine_chat_v1';
  const DEBOUNCE_MS = 450;

  const panel = document.getElementById('ai-panel');
  if (!panel) return;

  const endpoint = panel.dataset.chatEndpoint || '/chat/ai/';
  const csrfToken = panel.dataset.csrf || '';
  const isAuthed = String(panel.dataset.authed || '') === '1';

  let chatOpen = false;
  /** @type {{role: string, content: string}[]} */
  let chatHistory = [];
  /** @type {{mode: string, bike_step: string|null, data: object}} */
  let wizardState = { mode: 'none', bike_step: null, data: {} };
  /** @type {string[]} */
  let quickChips = [];
  let lastSendAt = 0;

  function defaultWizard() {
    return { mode: 'none', bike_step: null, data: {} };
  }

  function saveState() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          v: 1,
          messages: chatHistory,
          wizardState,
          quickChips,
        })
      );
    } catch (e) {
      /* ignore quota */
    }
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const data = JSON.parse(raw);
      if (data.v !== 1 || !Array.isArray(data.messages)) return;
      chatHistory = data.messages;
      wizardState = data.wizardState || defaultWizard();
      quickChips = Array.isArray(data.quickChips) ? data.quickChips : [];
    } catch (e) {
      /* ignore */
    }
  }

  function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function linkifyAssistantHtml(escaped) {
    let s = escaped;
    const placeholders = [];
    
    function addPlaceholder(html) {
        placeholders.push(html);
        return '%%LINK_' + (placeholders.length - 1) + '%%';
    }

    // Markdown-style links: [text](url) where url can be absolute or site-relative
    s = s.replace(/\[([^\]]+)\]\(((?:https?:\/\/|\/)[^)]+)\)/g, function (_, text, url) {
      return addPlaceholder('<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + text + '</a>');
    });
    // Wizard legacy format: "1. Назва — 25000 грн → https://..."
    s = s.replace(
      /(^|\n)(\d+\.\s*)([^<\n]+?)\s+—\s+([\d\s]+)\s*грн\s*→\s*(https?:\/\/[^\s<]+)/g,
      function (_, p0, idx, name, price, url) {
        return (
          p0 +
          idx +
          addPlaceholder('<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + name.trim() + '</a>') +
          ' — ' +
          price.trim() +
          ' грн'
        );
      }
    );
    // Generic "Назва (https://...)" → make only name clickable
    s = s.replace(/([^<\n]+?)\s*\((https?:\/\/[^\s<]+)\)/g, function (_, name, url) {
      const t = (name || '').trim();
      if (!t) return '(' + url + ')';
      return addPlaceholder('<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + t + '</a>');
    });
    // Helper to strip trailing punctuation/entities from URLs
    function extractUrlAndSuffix(m) {
      let url = m;
      let suffix = '';
      const badEndings = ['&quot;', '&gt;', '&lt;', '.', ',', ')', '"', "'"];
      let changed = true;
      while(changed) {
          changed = false;
          for(let i=0; i<badEndings.length; i++) {
              if(url.endsWith(badEndings[i])) {
                  suffix = badEndings[i] + suffix;
                  url = url.slice(0, -badEndings[i].length);
                  changed = true;
              }
          }
      }
      return { url: url, suffix: suffix };
    }

    // Raw URLs
    s = s.replace(/(https?:\/\/[^\s<]+)/g, function (m) {
      const parsed = extractUrlAndSuffix(m);
      return addPlaceholder('<a href="' + parsed.url + '" target="_blank" rel="noopener noreferrer">' + parsed.url + '</a>') + parsed.suffix;
    });
    
    // Relative paths
    s = s.replace(/(^|[\s(>])(\/(?:product|catalog|trails|stores)\/[^\s<]*)/g, function (_, p1, p2) {
      const parsed = extractUrlAndSuffix(p2);
      return p1 + addPlaceholder('<a href="' + parsed.url + '">' + parsed.url + '</a>') + parsed.suffix;
    });

    // Restore placeholders
    placeholders.forEach(function(html, i) {
        s = s.replace('%%LINK_' + i + '%%', html);
    });

    return s;
  }

  function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    requestAnimationFrame(function () {
      container.scrollTop = container.scrollHeight;
    });
  }

  function renderChips() {
    const wrap = document.getElementById('chat-quick-btns');
    if (!wrap) return;
    wrap.innerHTML = '';
    quickChips.forEach(function (text) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'quick-chip';
      btn.textContent = text;
      btn.addEventListener('click', function () {
        sendQuick(text);
      });
      wrap.appendChild(btn);
    });
  }

  function renderProductCardsHtml(products) {
    if (!products || !products.length) return '';
    const parts = ['<div class="chat-product-cards">'];
    products.forEach(function (p) {
      const img = p.image
        ? '<div class="chat-product-card__img"><img src="' +
          escapeHtml(p.image) +
          '" alt="" loading="lazy"></div>'
        : '';
      parts.push(
        '<a class="chat-product-card" href="' +
          escapeHtml(p.url) +
          '">' +
          img +
          '<div class="chat-product-card__body"><div class="chat-product-card__name">' +
          escapeHtml(p.name) +
          '</div><div class="chat-product-card__meta">' +
          escapeHtml(p.bike_type || '') +
          '</div><div class="chat-product-card__price">' +
          escapeHtml(String(p.price)) +
          ' грн</div></div></a>'
      );
    });
    parts.push('</div>');
    return parts.join('');
  }

  /**
   * @param {string} text
   * @param {'user'|'bot'} role
   * @param {{ productsHtml?: string }} [options]
   */
  function addMsg(text, role, options) {
    options = options || {};
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'msg msg--appear ' + role;
    let body = escapeHtml(text);
    if (role === 'bot') body = linkifyAssistantHtml(body);
    const safe = body.replace(/\n/g, '<br>');
    const av =
      role === 'bot'
        ? '<div class="msg-avatar" aria-hidden="true">AI</div>'
        : '<div class="msg-avatar" aria-hidden="true">Ви</div>';
    const extra = options.productsHtml || '';
    div.innerHTML = av + '<div class="msg-bubble"><div class="msg-text">' + safe + '</div>' + extra + '</div>';
    container.appendChild(div);
    scrollToBottom();
  }

  function showTyping() {
    const container = document.getElementById('chat-messages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'msg bot msg--typing';
    div.id = id;
    div.setAttribute('aria-live', 'polite');
    div.innerHTML =
      '<div class="msg-avatar" aria-hidden="true">AI</div>' +
      '<div class="typing-wrap">' +
      '<span class="typing-label">AI друкує…</span>' +
      '<div class="typing-indicator" aria-hidden="true">' +
      '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>' +
      '</div></div>';
    container.appendChild(div);
    scrollToBottom();
    return id;
  }

  function hideTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function setAssistantOpen(open) {
    chatOpen = open;
    const p = document.getElementById('ai-panel');
    const b = document.getElementById('ai-backdrop');
    if (p) p.classList.toggle('open', chatOpen);
    if (b) b.classList.toggle('open', chatOpen);
    document.body.style.overflow = chatOpen ? 'hidden' : '';
    if (chatOpen) {
      const inp = document.getElementById('chat-input');
      if (inp) inp.focus();
      scrollToBottom();
    }
  }

  function toggleChat() {
    setAssistantOpen(!chatOpen);
  }

  function ensureAssistantOpen() {
    if (!chatOpen) setAssistantOpen(true);
  }

  function applyChipWizardHint(text) {
    if (text === 'Інший бюджет' || text === 'Розумний підбір велосипеда') {
      wizardState = { mode: 'bike', bike_step: 'budget', data: {} };
    }
  }

  async function sendQuick(msg) {
    ensureAssistantOpen();
    applyChipWizardHint(msg);
    const input = document.getElementById('chat-input');
    if (input) input.value = msg;
    await sendMessage();
  }

  async function sendMessage() {
    const now = Date.now();
    if (now - lastSendAt < DEBOUNCE_MS) return;
    lastSendAt = now;

    const input = document.getElementById('chat-input');
    const text = (input && input.value ? input.value : '').trim();
    if (!text) return;

    if (input) input.value = '';
    addMsg(text, 'user');
    chatHistory.push({ role: 'user', content: text });
    saveState();

    const typingId = showTyping();

    try {
      const resp = await fetch(endpoint, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          message: text,
          messages: chatHistory.slice(-20),
          wizard_state: wizardState,
          client_ts: now,
        }),
      });
      const data = await resp.json();
      hideTyping(typingId);

      if (data.wizard_state) wizardState = data.wizard_state;
      if (Array.isArray(data.quick_chips) && data.quick_chips.length) {
        quickChips = data.quick_chips;
      }

      const reply = data.response || data.error || 'Не вдалося отримати відповідь.';
      const products = data.recommended_products || [];
      const productsHtml = renderProductCardsHtml(products);
      addMsg(reply, 'bot', { productsHtml });
      chatHistory.push({ role: 'assistant', content: reply });
      saveState();
      renderChips();
    } catch (e) {
      hideTyping(typingId);
      addMsg('Помилка мережі. Спробуйте ще раз.', 'bot');
    }
  }

  function clearChat() {
    chatHistory = [];
    wizardState = defaultWizard();
    quickChips = isAuthed
      ? ['Розумний підбір велосипеда', 'Екіпірування для початківця', 'Траси поруч', 'Підібрати велосипед']
      : ['Каталог', 'Екіпірування для початківця', 'Підібрати велосипед', 'Як обрати розмір'];
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      /* ignore */
    }
    const container = document.getElementById('chat-messages');
    if (container) {
      container.innerHTML =
        '<div class="msg bot msg--appear">' +
        '<div class="msg-avatar" aria-hidden="true">AI</div>' +
        '<div class="msg-bubble"><div class="msg-text">Вітаю! Я AI-консультант VeloUkraine. Оберіть підказку або напишіть запит — збережу контекст між відвідуваннями.</div></div></div>';
    }
    saveState();
    renderChips();
    scrollToBottom();
  }

  function restoreMessagesFromStorage() {
    const container = document.getElementById('chat-messages');
    if (!container || !chatHistory.length) return;
    container.innerHTML = '';
    chatHistory.forEach(function (m) {
      const role = m.role === 'user' ? 'user' : 'bot';
      addMsg(m.content, role, {});
    });
  }

  // --- init ---
  loadState();
  if (chatHistory.length) {
    restoreMessagesFromStorage();
  }
  if (!quickChips.length) {
    quickChips = isAuthed
      ? ['Розумний підбір велосипеда', 'Підібрати велосипед', 'Траси поруч', 'Екіпірування для початківця']
      : ['Підібрати велосипед', 'Каталог', 'Екіпірування для початківця', 'Як обрати розмір'];
  }
  renderChips();

  const inputEl = document.getElementById('chat-input');
  if (inputEl) {
    inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  document.getElementById('chat-clear')?.addEventListener('click', clearChat);

  window.toggleChat = toggleChat;
  window.sendMessage = sendMessage;
  window.sendQuick = sendQuick;
})();
