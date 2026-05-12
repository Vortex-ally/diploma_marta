/**
 * Product gallery: click thumbnails to change main image.
 * - No dependencies
 * - Keyboard support (ArrowLeft/ArrowRight when focused)
 */
(function () {
  function initGallery(root) {
    const mainWrap = root.querySelector('[data-gallery="main"]');
    const mainImg = root.querySelector('[data-gallery-main]');
    const thumbs = Array.from(root.querySelectorAll('[data-gallery-thumb]'));
    if (!mainImg || !thumbs.length) return;

    const colorLabel = document.querySelector('[data-color-selected]');

    // --- zoom (hover) ---
    // UX: zoom toggles on pointer enter, disables on leave; transform-origin follows cursor.
    if (mainWrap) {
      mainWrap.dataset.zoom = 'off';

      function setOriginFromEvent(e) {
        const rect = mainWrap.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        const cx = Math.max(0, Math.min(100, x));
        const cy = Math.max(0, Math.min(100, y));
        mainImg.style.transformOrigin = cx + '% ' + cy + '%';
      }

      mainWrap.addEventListener('pointerenter', (e) => {
        mainWrap.dataset.zoom = 'on';
        setOriginFromEvent(e);
      });
      mainWrap.addEventListener('pointermove', (e) => {
        if (mainWrap.dataset.zoom !== 'on') return;
        setOriginFromEvent(e);
      });
      mainWrap.addEventListener('pointerleave', () => {
        mainWrap.dataset.zoom = 'off';
        mainImg.style.transformOrigin = '50% 50%';
      });
    }

    function setActive(idx) {
      const btn = thumbs[idx];
      if (!btn) return;
      const src = btn.getAttribute('data-src') || '';
      if (!src) return;

      mainImg.src = src;
      const colorName = btn.getAttribute('data-color-name') || '';
      if (colorLabel && colorName) colorLabel.textContent = colorName;
      if (mainWrap) {
        mainWrap.dataset.zoom = 'off';
        mainImg.style.transformOrigin = '50% 50%';
      }
      thumbs.forEach((t) => t.classList.remove('active'));
      btn.classList.add('active');

      // keep the active thumb visible in a horizontal scroll row
      try {
        btn.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' });
      } catch (e) {
        /* ignore */
      }
    }

    thumbs.forEach((btn, idx) => {
      btn.addEventListener('click', () => setActive(idx));
      btn.addEventListener('keydown', (e) => {
        if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
        e.preventDefault();
        const delta = e.key === 'ArrowRight' ? 1 : -1;
        const next = (idx + delta + thumbs.length) % thumbs.length;
        thumbs[next].focus();
        setActive(next);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.product-gallery').forEach(initGallery);
  });
})();

