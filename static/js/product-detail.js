/**
 * Product detail UX:
 * - Size picker (shoes/clothing): selectable boxes, persists per product.
 * - Size chart modal (simple, type-specific).
 */
(function () {
  const LS_KEY = 'veloukraine_size_v1';

  function loadMap() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      const data = raw ? JSON.parse(raw) : {};
      return data && typeof data === 'object' ? data : {};
    } catch (e) {
      return {};
    }
  }

  function saveMap(map) {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(map));
    } catch (e) {
      /* ignore */
    }
  }

  function inferTypeFromDom(picker) {
    const t = picker?.getAttribute('data-size-type') || '';
    if (t) return t;
    // fallback heuristic: tag “Вело-туфлі” exists => shoes, else clothing
    const tag = document.querySelector('.sizes-block .tag.tag-blue');
    return tag ? 'shoes' : 'clothing';
  }

  function buildChartHtml(type) {
    if (type === 'shoes') {
      return (
        '<p style="color:#64748b; margin-bottom:10px;">EU → довжина стопи (см). Орієнтовно, залежить від бренду.</p>' +
        '<table class="size-table" aria-label="Розмірна сітка туфлів">' +
        '<thead><tr><th>EU</th><th>см</th></tr></thead>' +
        '<tbody>' +
        '<tr><td>36</td><td>23.0</td></tr>' +
        '<tr><td>37</td><td>23.7</td></tr>' +
        '<tr><td>38</td><td>24.0</td></tr>' +
        '<tr><td>39</td><td>24.7</td></tr>' +
        '<tr><td>40</td><td>25.3</td></tr>' +
        '<tr><td>41</td><td>26.0</td></tr>' +
        '<tr><td>42</td><td>26.7</td></tr>' +
        '<tr><td>43</td><td>27.3</td></tr>' +
        '<tr><td>44</td><td>28.0</td></tr>' +
        '<tr><td>45</td><td>28.7</td></tr>' +
        '</tbody></table>'
      );
    }

    if (type === 'helmet') {
      return (
        '<p style="color:#64748b; margin-bottom:10px;">Орієнтовно. Якщо між розмірами — бери більший.</p>' +
        '<table class="size-table" aria-label="Розмірна сітка шоломів">' +
        '<thead><tr><th>Розмір</th><th>Окружність голови (см)</th></tr></thead>' +
        '<tbody>' +
        '<tr><td>XS</td><td>51–53</td></tr>' +
        '<tr><td>S</td><td>54–56</td></tr>' +
        '<tr><td>M</td><td>57–59</td></tr>' +
        '<tr><td>L</td><td>60–62</td></tr>' +
        '<tr><td>XL</td><td>63–65</td></tr>' +
        '</tbody></table>'
      );
    }

    if (type === 'bike') {
      return (
        '<p style="color:#64748b; margin-bottom:10px;">Розмір рами залежить від росту, геометрії та посадки. Для точності — звіряйся з таблицею бренду.</p>' +
        '<table class="size-table" aria-label="Підбір розміру велосипеда">' +
        '<thead><tr><th>Розмір</th><th>Зріст (см)</th></tr></thead>' +
        '<tbody>' +
        '<tr><td>XS</td><td>155–165</td></tr>' +
        '<tr><td>S</td><td>165–175</td></tr>' +
        '<tr><td>M</td><td>175–185</td></tr>' +
        '<tr><td>L</td><td>185–195</td></tr>' +
        '<tr><td>XL</td><td>195–205</td></tr>' +
        '</tbody></table>'
      );
    }

    // clothing (simplified)
    return (
      '<p style="color:#64748b; margin-bottom:10px;">Орієнтовна розмірна сітка (унісекс). Для точності звіряйся з брендом.</p>' +
      '<table class="size-table" aria-label="Розмірна сітка одягу">' +
      '<thead><tr><th>Розмір</th><th>Груди (см)</th><th>Талія (см)</th></tr></thead>' +
      '<tbody>' +
      '<tr><td>XS</td><td>82–86</td><td>66–70</td></tr>' +
      '<tr><td>S</td><td>86–92</td><td>70–76</td></tr>' +
      '<tr><td>M</td><td>92–98</td><td>76–82</td></tr>' +
      '<tr><td>L</td><td>98–104</td><td>82–88</td></tr>' +
      '<tr><td>XL</td><td>104–110</td><td>88–94</td></tr>' +
      '<tr><td>XXL</td><td>110–116</td><td>94–100</td></tr>' +
      '</tbody></table>'
    );
  }

  function ensureModal() {
    let backdrop = document.querySelector('[data-size-chart-backdrop]');
    if (backdrop) return backdrop;

    backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.setAttribute('data-size-chart-backdrop', '1');
    backdrop.innerHTML =
      '<div class="modal" role="dialog" aria-modal="true" aria-label="Таблиця розмірів">' +
      '<div class="modal-head">' +
      '<strong>Таблиця розмірів</strong>' +
      '<button type="button" class="modal-close" data-size-chart-close aria-label="Закрити">✕</button>' +
      '</div>' +
      '<div class="modal-body" data-size-chart-body></div>' +
      '</div>';

    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) backdrop.classList.remove('open');
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') backdrop.classList.remove('open');
    });
    document.body.appendChild(backdrop);
    return backdrop;
  }

  function initSizePicker() {
    const picker = document.querySelector('[data-size-picker]');
    if (!picker) return;

    const slug = picker.getAttribute('data-product-slug') || 'unknown';
    const selectedLabel = document.querySelector('[data-size-selected]');
    const boxes = Array.from(picker.querySelectorAll('[data-size]'));

    const map = loadMap();
    const saved = map[slug];

    function apply(size) {
      boxes.forEach((b) => b.classList.toggle('active', b.getAttribute('data-size') === size));
      if (selectedLabel) selectedLabel.textContent = size ? size : 'Оберіть';
      map[slug] = size || '';
      saveMap(map);
    }

    if (saved) apply(saved);

    boxes.forEach((b) => {
      b.addEventListener('click', () => {
        const size = b.getAttribute('data-size') || '';
        apply(size);
      });
    });

    const openBtn = document.querySelector('[data-size-chart-open]');
    if (openBtn) {
      openBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const type = inferTypeFromDom(picker);
        const backdrop = ensureModal();
        const body = backdrop.querySelector('[data-size-chart-body]');
        if (body) body.innerHTML = buildChartHtml(type);
        backdrop.classList.add('open');

        backdrop.querySelector('[data-size-chart-close]')?.addEventListener('click', () => {
          backdrop.classList.remove('open');
        });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    initSizePicker();
  });
})();

