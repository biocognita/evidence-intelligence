// Shared frontend utilities for the Evidence Intelligence pages.
//
// 1. localStorage TTL cache — lets both the search page and the claim
//    report page render instantly on repeat visits without re-hitting the
//    server (or Google Sheets). TTL defaults to 5 minutes, mirroring the
//    backend cache, so staleness stays bounded.
//
// 2. highlightText() — case-insensitive match highlighting built from DOM
//    text nodes + <mark> elements (never innerHTML), so anything coming
//    from the Google Sheet is XSS-safe.

const DEFAULT_CACHE_TTL_MS = 5 * 60 * 1000;

// Query once at load (not per transition) — cheap, and identical for the
// life of the page.
const prefersReducedMotion =
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ----- localStorage cache helpers (best-effort) -----

function cacheKey(prefix, ...parts) {
    // Lowercase so ?q=Sleep and ?q=sleep share one entry.
    const joined = parts.map((part) => String(part).toLowerCase()).join("|");
    return `${prefix}:${joined}`;
}

function readCache(key, ttlMs = DEFAULT_CACHE_TTL_MS) {
    try {
        const raw = localStorage.getItem(key);
        if (!raw) {
            return null;
        }
        const entry = JSON.parse(raw);
        if (!entry || typeof entry.fetched_at !== "number") {
            return null;
        }
        if (Date.now() - entry.fetched_at > ttlMs) {
            return null;
        }
        return entry.value;
    } catch (err) {
        return null; // storage unavailable / corrupt — just fetch
    }
}

function writeCache(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify({
            fetched_at: Date.now(),
            value: value
        }));
    } catch (err) {
        // Quota exceeded / disabled — caching is best-effort
    }
}

function clearCache(key) {
    try {
        localStorage.removeItem(key);
    } catch (err) {
        // best-effort
    }
}

// ----- Display helpers -----

// The project's claims read better in Title Case (the owner's preference),
// so capitalize the first letter of every word: "Melatonin improves sleep
// quality" -> "Melatonin Improves Sleep Quality". Non-letters (IDs,
// numbers, dashes) are left untouched.
function toTitleCase(text) {
    return String(text || "").replace(/\w\S*/g, (word) => {
        return word.charAt(0).toUpperCase() + word.slice(1);
    });
}

// ----- Match-highlight dismissal -----

// The search-match highlights are a "here's why this matched" hint, not
// decoration: they remove themselves on the first click, on scroll, or
// after a few seconds — and can be brought back by clicking the query
// chip on the results page.

let matchHighlightsDismissed = false;
let matchHighlightTimer = null;

function unwrapHighlightMarks() {
    document.querySelectorAll("mark.match-highlight").forEach((mark) => {
        const text = document.createTextNode(mark.textContent);
        mark.replaceWith(text);
    });
}

// Fade the marks out (opacity 0, via CSS transition), then unwrap them
// back into plain text. Reduced-motion users skip the animation.
function dismissMatchHighlights() {
    matchHighlightsDismissed = true;
    if (matchHighlightTimer) {
        clearTimeout(matchHighlightTimer);
        matchHighlightTimer = null;
    }
    const marks = document.querySelectorAll("mark.match-highlight");
    if (!marks.length) {
        return;
    }
    if (prefersReducedMotion) {
        unwrapHighlightMarks();
        return;
    }
    marks.forEach((mark) => mark.classList.add("match-highlight--fading"));
    setTimeout(unwrapHighlightMarks, 450);
}

// The one-shot dismissal wiring shared by initMatchHighlightDismissal()
// (first call on the page) and armHighlightDismissal() (re-arms after a
// query-chip re-highlight).
function armHighlightDismissal() {
    document.addEventListener("click", dismissMatchHighlights, { once: true });
    document.addEventListener("scroll", dismissMatchHighlights, { once: true, passive: true });
    if (matchHighlightTimer) {
        clearTimeout(matchHighlightTimer);
    }
    matchHighlightTimer = setTimeout(dismissMatchHighlights, 8000);
}

// Call once per page: dismiss on first click, first scroll, or after 8
// seconds so highlights never linger.
function initMatchHighlightDismissal() {
    armHighlightDismissal();
}

// After rendering new content (e.g. "Load more" cards), strip highlights
// if the user already dismissed them, so freshly-added cards match the
// rest of the page.
function purgeDismissedHighlights() {
    if (!matchHighlightsDismissed) {
        return;
    }
    unwrapHighlightMarks();
}

// ----- Page transitions -----

// Cross-page fades: clicking an internal link fades the current page
// out, then navigates; the destination page fades itself in on load.
// Reduced-motion users get plain instant navigation instead.

let pageTransitionRunning = false;

// Fade the current page out, then navigate. Falls back to an instant
// jump if reduced-motion is on or a transition is already running.
function transitionTo(url) {
    if (prefersReducedMotion || pageTransitionRunning) {
        window.location.href = url;
        return;
    }
    pageTransitionRunning = true;
    document.body.classList.add("page-leaving");
    window.setTimeout(() => {
        window.location.href = url;
    }, 230);
}

function initPageTransitions() {
    if (prefersReducedMotion) {
        return;
    }

    // Fade the just-loaded page in. Also covers back/forward navigation
    // (the class is added every load, before the first paint).
    const body = document.body;
    if (body && !body.classList.contains("page-enter-done")) {
        body.classList.add("page-entering");
        requestAnimationFrame(() => {
            requestAnimationFrame(() => body.classList.add("page-enter-done"));
        });
    }

    // Intercept internal link clicks so navigation cross-fades. Anchor
    // (#section), mailto, external, and target=_blank links are left alone.
    document.addEventListener("click", (event) => {
        const link = event.target.closest ? event.target.closest("a") : null;
        if (!link) {
            return;
        }
        // Never hijack modified clicks (ctrl/cmd/shift/open-in-new-tab)
        // or middle-button clicks — let the browser do its normal thing.
        if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
        }
        const href = link.getAttribute("href") || "";
        if (!href || href.charAt(0) === "#" || /^(mailto:|tel:|javascript:)/i.test(href)) {
            return;
        }
        if (link.target && link.target !== "_self") {
            return;
        }
        if (link.hasAttribute("download")) {
            return;
        }
        let url;
        try {
            url = new URL(link.href, window.location.href);
        } catch (err) {
            return;
        }
        if (url.origin !== window.location.origin) {
            return;
        }
        event.preventDefault();
        transitionTo(url.href);
    }, true);
}

// Auto-run: every page that loads cache_utils.js gets cross-page fades.
initPageTransitions();

// ----- Scroll reveal -----

// Fade .reveal elements in as they scroll into view (the About Us /
// Methodology / Contact cards on the home page, and the footer on every
// page). Reduced-motion users are handled in CSS, which forces .reveal
// to stay fully visible, so this only ever adds the class.
function initScrollReveal() {
    const revealEls = document.querySelectorAll(".reveal");
    if (!revealEls.length) {
        return; // no reveal elements on this page
    }
    if (!("IntersectionObserver" in window)) {
        revealEls.forEach((el) => el.classList.add("visible"));
        return;
    }
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.2 }
    );
    revealEls.forEach((el) => observer.observe(el));
}

// Auto-run: every page that loads cache_utils.js gets the scroll reveal.
initScrollReveal();

// ----- XSS-safe match highlighting -----

// Splits `text` into plain text nodes and <mark> elements so the query can
// never be injected as HTML. Query matching is case-insensitive.
function highlightText(text, query) {
    const frag = document.createDocumentFragment();
    if (!query || !text) {
        frag.appendChild(document.createTextNode(text || ""));
        return frag;
    }
    const lowerText = text.toLowerCase();
    const lowerQuery = query.toLowerCase();
    let start = 0;
    let index;
    while ((index = lowerText.indexOf(lowerQuery, start)) !== -1) {
        if (index > start) {
            frag.appendChild(document.createTextNode(text.slice(start, index)));
        }
        const mark = document.createElement("mark");
        mark.className = "match-highlight";
        mark.textContent = text.slice(index, index + query.length);
        frag.appendChild(mark);
        start = index + query.length;
    }
    if (start < text.length) {
        frag.appendChild(document.createTextNode(text.slice(start)));
    }
    return frag;
}
