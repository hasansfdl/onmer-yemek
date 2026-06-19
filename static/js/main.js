/* =================================================================
   ONMER YEMEK ORGANİZASYON — site-wide JS
   - Page loader
   - Sticky / scroll-aware navbar
   - Smooth scroll
   - GLightbox init (gallery)
   - Scroll-to-top button
   - Toast auto-show
   - Reservation slot live lookup
   ================================================================= */

(function () {
    'use strict';

    /* ---------- 1. Page loader ---------- */
    window.addEventListener('load', function () {
        const loader = document.getElementById('page-loader');
        if (!loader) return;
        // Debug helper: append `?freeze_loader=1` to keep the loader visible
        // (useful when capturing a screenshot of the splash animation).
        if (new URLSearchParams(location.search).has('freeze_loader')) return;
        // Smooth fade out, then fully hide
        setTimeout(() => loader.classList.add('hidden'), 350);
        setTimeout(() => { loader.style.display = 'none'; }, 1200);
    });

    /* ---------- 2. Navbar scroll behaviour ---------- */
    const navbar = document.getElementById('mainNavbar');
    const onScroll = () => {
        if (!navbar) return;
        if (window.scrollY > 60) navbar.classList.add('scrolled');
        else navbar.classList.remove('scrolled');

        const top = document.getElementById('scrollTopBtn');
        if (top) {
            if (window.scrollY > 600) top.classList.add('visible');
            else top.classList.remove('visible');
        }
    };
    document.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    /* ---------- 3. Smooth scroll for in-page anchors ---------- */
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
        const href = a.getAttribute('href');
        if (!href || href === '#' || href.length < 2) return;
        a.addEventListener('click', (e) => {
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                window.scrollTo({
                    top: target.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    /* ---------- 4. Scroll-to-top button ---------- */
    const topBtn = document.getElementById('scrollTopBtn');
    if (topBtn) {
        topBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    /* ---------- 5. GLightbox ---------- */
    if (window.GLightbox) {
        GLightbox({
            selector: '.glightbox',
            touchNavigation: true,
            loop: true,
            zoomable: true,
        });
    }

    /* ---------- 6. Bootstrap toast auto-show ---------- */
    document.querySelectorAll('.toast').forEach(t => {
        try {
            const toast = bootstrap.Toast.getOrCreateInstance(t);
            toast.show();
        } catch (e) { /* noop */ }
    });

    /* ---------- 7. Filter chips: client-side category filter (dishes) ---------- */
    document.querySelectorAll('[data-filter-target]').forEach(chip => {
        chip.addEventListener('click', (ev) => {
            ev.preventDefault();
            const targetSel = chip.dataset.filterTarget;
            const cat = chip.dataset.category || 'all';
            const grid = document.querySelector(targetSel);
            if (!grid) return;

            grid.querySelectorAll('[data-cat]').forEach(item => {
                if (cat === 'all' || item.dataset.cat === cat) {
                    item.style.display = '';
                    item.classList.remove('d-none');
                } else {
                    item.classList.add('d-none');
                }
            });

            // active chip
            const group = chip.closest('.filter-chips');
            if (group) {
                group.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            }
            chip.classList.add('active');
        });
    });

    /* ---------- 8. Reservation: live slot lookup ---------- */
    const dateField = document.getElementById('id_date');
    const timeField = document.getElementById('id_time');
    const slotsUrl  = document.querySelector('[data-slots-url]')?.dataset.slotsUrl;

    if (dateField && timeField && slotsUrl) {
        const refreshSlots = () => {
            const v = dateField.value;
            if (!v) return;
            fetch(`${slotsUrl}?date=${encodeURIComponent(v)}`)
                .then(r => r.json())
                .then(data => {
                    const taken = new Set(data.taken || []);
                    Array.from(timeField.options).forEach(opt => {
                        if (taken.has(opt.value)) {
                            opt.disabled = true;
                            if (!opt.textContent.includes('(Dolu)')) {
                                opt.textContent = `${opt.value} (Dolu)`;
                            }
                        } else {
                            opt.disabled = false;
                            opt.textContent = opt.value;
                        }
                    });
                })
                .catch(() => { /* noop */ });
        };
        dateField.addEventListener('change', refreshSlots);
        if (dateField.value) refreshSlots();
    }
})();
