/**
 * Product comparison: localStorage, bottom bar, max 4 items.
 * Buttons use data-compare-add + data-compare-id, name, image, url.
 */
(function () {
  var STORAGE = 'veloukraine_compare_v1';
  var MAX = 4;

  function load() {
    try {
      var r = localStorage.getItem(STORAGE);
      var d = r ? JSON.parse(r) : [];
      return Array.isArray(d) ? d : [];
    } catch (e) {
      return [];
    }
  }

  function save(items) {
    try {
      localStorage.setItem(STORAGE, JSON.stringify(items));
    } catch (e) {
      /* ignore */
    }
  }

  function esc(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function findBar() {
    return document.getElementById('compare-bar');
  }

  function isAuthed() {
    var bar = findBar();
    if (!bar) return false;
    return String(bar.getAttribute('data-authed') || '') === '1';
  }

  function loginUrl() {
    var bar = findBar();
    if (!bar) return '/login/';
    return String(bar.getAttribute('data-login-url') || '/login/');
  }

  function setFabOffset(on) {
    var fab = document.getElementById('ai-fab');
    if (!fab) return;
    if (on) {
      fab.classList.add('ai-fab--above-compare');
    } else {
      fab.classList.remove('ai-fab--above-compare');
    }
  }

  function buildQuery(items) {
    var parts = [];
    for (var i = 0; i < items.length; i++) {
      parts.push('products=' + encodeURIComponent(String(items[i].id)));
    }
    return parts.length ? '/compare/?' + parts.join('&') : '/compare/';
  }

  function render() {
    var items = load();
    var bar = findBar();
    if (!bar) return;
    if (items.length === 0) {
      bar.hidden = true;
      bar.classList.remove('compare-bar--open');
      document.body.classList.remove('compare-bar-on');
      document.body.classList.remove('compare-bar-tall');
      setFabOffset(false);
      return;
    }
    bar.hidden = false;
    document.body.classList.add('compare-bar-on');
    setFabOffset(true);
    document.body.classList.toggle('compare-bar-tall', bar.classList.contains('compare-bar--open'));

    var elCount = bar.querySelector('[data-compare-count]');
    if (elCount) {
      elCount.textContent = 'ПОРІВНЯТИ ТОВАРИ (' + items.length + '/' + MAX + ')';
    }
    var slots = bar.querySelector('[data-compare-slots]');
    if (slots) {
      slots.innerHTML = '';
      var changed = false;
      for (var s = 0; s < MAX; s++) {
        var it = items[s];
        var slot = document.createElement('div');
        if (it) {
          slot.className = 'compare-bar__slot compare-bar__slot--filled';
          // Self-heal: older stored items may have empty or stale /media/ image.
          // If current page has a compare button for this product, reuse its data-compare-image.
          var isStaleImage = !it.image || it.image.indexOf('/media/') === 0;
          if (isStaleImage) {
            try {
              var btn = document.querySelector(
                '[data-compare-add][data-compare-id="' + String(it.id) + '"]'
              );
              if (btn) {
                var live = (btn.getAttribute('data-compare-image') || '').trim();
                if (live) {
                  it.image = live;
                  changed = true;
                }
              }
            } catch (e) {
              /* ignore */
            }
          }
          var imgBlock = it.image
            ? '<div class="compare-bar__slot-img"><img src="' + esc(it.image) + '" alt=""></div>'
            : '<div class="compare-bar__slot-img compare-bar__slot-img--empty">Немає фото</div>';
          slot.innerHTML =
            '<button type="button" class="compare-bar__remove" data-compare-remove="' +
            it.id +
            '" aria-label="Прибрати">×</button>' +
            imgBlock +
            '<div class="compare-bar__slot-name">' +
            esc(it.name) +
            '</div>';
        } else {
          slot.className = 'compare-bar__slot compare-bar__slot--empty';
          slot.innerHTML = '<span class="compare-bar__empty-mark"></span>';
        }
        slots.appendChild(slot);
      }
      if (changed) save(items);
      var removes = slots.querySelectorAll('[data-compare-remove]');
      for (var r = 0; r < removes.length; r++) {
        removes[r].addEventListener('click', function (e) {
          e.preventDefault();
          var id = parseInt(this.getAttribute('data-compare-remove'), 10);
          removeId(id);
        });
      }
    }
    var go = bar.querySelector('[data-compare-go]');
    if (go) {
      if (items.length >= 2) {
        var dest = buildQuery(items);
        if (isAuthed()) {
          go.setAttribute('href', dest);
        } else {
          go.setAttribute('href', loginUrl() + '?next=' + encodeURIComponent(dest));
        }
        go.classList.remove('compare-bar__go--disabled');
        go.setAttribute('aria-disabled', 'false');
      } else {
        go.setAttribute('href', '#');
        go.classList.add('compare-bar__go--disabled');
        go.setAttribute('aria-disabled', 'true');
        go.setAttribute('title', 'Оберіть щонайменше 2 товари');
      }
    }
    var strip = bar.querySelector('[data-compare-toggle]');
    if (strip) {
      strip.setAttribute('aria-expanded', bar.classList.contains('compare-bar--open') ? 'true' : 'false');
    }
  }

  function addItem(raw) {
    var items = load();
    var id = parseInt(String(raw.id), 10);
    if (!id) return;
    for (var i = 0; i < items.length; i++) {
      if (items[i].id === id) {
        if (window.dispatchEvent) {
          window.dispatchEvent(
            new CustomEvent('velo-compare-toast', { detail: { type: 'exists' } })
          );
        }
        return;
      }
    }
    if (items.length >= MAX) {
      if (window.dispatchEvent) {
        window.dispatchEvent(
          new CustomEvent('velo-compare-toast', { detail: { type: 'full' } })
        );
      }
      return;
    }
    items.push({
      id: id,
      name: (raw.name || '').trim() || 'Товар',
      image: (raw.image || '').trim(),
      url: (raw.url || '').trim() || '/',
    });
    save(items);
    render();
    var bar = findBar();
    if (bar) bar.classList.add('compare-bar--open');
  }

  function removeId(id) {
    var items = load().filter(function (x) {
      return x.id !== id;
    });
    save(items);
    render();
  }

  function clearAll() {
    save([]);
    render();
  }

  document.addEventListener('click', function (e) {
    var btn = e.target && e.target.closest && e.target.closest('[data-compare-add]');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    var img = btn.getAttribute('data-compare-image') || '';
    if (!img || img.indexOf('/media/') === 0) {
      // Fallback: try to grab the visible product image from the same card/section.
      try {
        var root =
          btn.closest('.product-card') ||
          btn.closest('.product-actions') ||
          btn.closest('article') ||
          btn.closest('section') ||
          document;
        var pic =
          (root && root.querySelector && root.querySelector('img')) ? root.querySelector('img') : null;
        if (pic && pic.getAttribute) {
          img = (pic.getAttribute('src') || '').trim();
        }
      } catch (err) {
        /* ignore */
      }
    }
    addItem({
      id: btn.getAttribute('data-compare-id'),
      name: btn.getAttribute('data-compare-name') || '',
      image: img,
      url: btn.getAttribute('data-compare-url') || '',
    });
  });

  document.addEventListener('click', function (e) {
    var t = e.target && e.target.closest && e.target.closest('[data-compare-toggle]');
    if (!t) return;
    e.preventDefault();
    var bar = findBar();
    if (!bar) return;
    bar.classList.toggle('compare-bar--open');
    t.setAttribute('aria-expanded', bar.classList.contains('compare-bar--open') ? 'true' : 'false');
    if (load().length > 0) {
      document.body.classList.toggle('compare-bar-tall', bar.classList.contains('compare-bar--open'));
    }
  });

  document.addEventListener('click', function (e) {
    var c = e.target && e.target.closest && e.target.closest('[data-compare-clear]');
    if (!c) return;
    e.preventDefault();
    clearAll();
  });

  document.addEventListener('click', function (e) {
    var g = e.target && e.target.closest && e.target.closest('[data-compare-go]');
    if (!g) return;
    if (g.classList.contains('compare-bar__go--disabled')) {
      e.preventDefault();
    }
  });

  document.addEventListener('DOMContentLoaded', render);
  window.addEventListener('storage', function (ev) {
    if (ev.key === STORAGE) render();
  });

  window.veloCompareAdd = addItem;
  window.veloCompareRender = render;
})();
