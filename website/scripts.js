// ----- Search (button click) -----

document
    .getElementById("search-button")
    .addEventListener("click", searchClaim);

// Navigate to the right page for a query. Claim IDs (C0001 / c0001) go
// straight to the report; anything else is a full search. Uses the page
// cross-fade when available (cache_utils.js), plain nav otherwise.
function searchClaim() {
    const query = document
        .getElementById("claim-input")
        .value
        .trim();

    if (!query) {
        return;
    }

    let url;
    if (/^c[0-9]{4}$/i.test(query)) {
        url = `reportpage.html?claim=${query.toUpperCase()}`;
    } else {
        const params = new URLSearchParams({ q: query });
        url = `searchpage.html?${params.toString()}`;
    }

    if (window.transitionTo) {
        window.transitionTo(url);
    } else {
        window.location.href = url;
    }
}

// ----- Search-as-you-type -----
//
// While the user types, a debounced call to the backend fills a small
// suggestion panel under the search bar: the top matching claims (with
// their ID + confidence pills) or the report itself when the query is a
// claim ID. Arrow keys move the highlight, Enter picks the highlighted
// row, Escape closes the panel. Out-of-date requests are aborted so a
// fast typist never sees stale results.

(function () {
    // Live suggestions belong to the home hero search bar. The search
    // results page has its own refine bar, but it already shows results
    // below — a dropdown there would be redundant.
    const input = document.getElementById("claim-input");
    const searchArea = input && input.closest(".searcharea");
    if (!input || !searchArea || !window.fetch || !document.querySelector(".home-title")) {
        return;
    }

    const panel = document.createElement("div");
    panel.className = "live-suggestions";
    panel.setAttribute("role", "listbox");
    panel.hidden = true;
    searchArea.appendChild(panel);

    let debounceTimer = null;
    let activeController = null;
    let highlightedIndex = -1;

    function closePanel() {
        panel.hidden = true;
        panel.innerHTML = "";
        highlightedIndex = -1;
        if (activeController) {
            activeController.abort();
            activeController = null;
        }
    }

    function goTo(url) {
        closePanel();
        if (window.transitionTo) {
            window.transitionTo(url);
        } else {
            window.location.href = url;
        }
    }

    function highlight(options) {
        options.forEach((el, i) => {
            el.classList.toggle("live-suggestion--active", i === highlightedIndex);
        });
        const active = options[highlightedIndex];
        if (active && active.scrollIntoView) {
            active.scrollIntoView({ block: "nearest" });
        }
    }

    function renderPanel(query, items) {
        panel.innerHTML = "";
        highlightedIndex = -1;

        const frag = document.createDocumentFragment();

        items.forEach((item, index) => {
            const row = document.createElement("button");
            row.type = "button";
            row.className = "live-suggestion";
            row.setAttribute("role", "option");
            row.dataset.index = String(index);

            const top = document.createElement("div");
            top.className = "live-suggestion-top";

            const idPill = document.createElement("span");
            idPill.className = "live-pill";
            idPill.textContent = item.type === "report"
                ? item.id
                : item.claim["Claim ID"];
            top.appendChild(idPill);

            const score = item.type === "report"
                ? item.score
                : item.claim.confidence_score;
            if (typeof score === "number") {
                const scorePill = document.createElement("span");
                scorePill.className = "live-pill live-pill--score";
                scorePill.textContent = `Confidence ${score}/100`;
                top.appendChild(scorePill);
            }

            const claimText = document.createElement("div");
            claimText.className = "live-suggestion-claim";
            if (item.type === "report") {
                claimText.textContent = toTitleCase(item.claim);
            } else {
                claimText.appendChild(
                    highlightText(toTitleCase(item.claim["Claim"] || ""), query)
                );
            }

            const meta = document.createElement("div");
            meta.className = "live-suggestion-meta";
            if (item.type === "report") {
                meta.textContent = "Open the full claim report";
            } else {
                const metaParts = [
                    item.claim["Intervention"],
                    item.claim["Outcome"],
                    item.claim["Population"]
                ].filter(Boolean);
                meta.textContent = metaParts.join(" · ") || "Claim report";
            }

            row.appendChild(top);
            row.appendChild(claimText);
            row.appendChild(meta);

            row.addEventListener("click", () => {
                const target = item.type === "report"
                    ? `reportpage.html?claim=${encodeURIComponent(item.id)}`
                    : `reportpage.html?claim=${encodeURIComponent(item.claim["Claim ID"])}`;
                goTo(target);
            });

            frag.appendChild(row);
        });

        const seeAll = document.createElement("a");
        seeAll.className = "live-see-all";
        seeAll.href = `searchpage.html?q=${encodeURIComponent(query)}`;
        const seeAllText = document.createElement("span");
        seeAllText.textContent = `See all results for “${query}”`;
        const seeAllArrow = document.createElement("span");
        seeAllArrow.textContent = "→";
        seeAll.appendChild(seeAllText);
        seeAll.appendChild(seeAllArrow);
        // The page-transition click handler (cache_utils.js) already
        // intercepts this same-origin link and fades to it — this own
        // listener only needs to close the panel, or the fade would be
        // cut short by a second navigation.
        seeAll.addEventListener("click", () => {
            closePanel();
        });
        frag.appendChild(seeAll);

        panel.appendChild(frag);
        panel.hidden = false;
    }

    async function fetchSuggestions(query) {
        if (activeController) {
            activeController.abort();
        }
        const controller = new AbortController();
        activeController = controller;

        let items = [];

        try {
            if (/^c[0-9]{4}$/i.test(query)) {
                // Claim ID → show the report itself as the suggestion
                const res = await fetch(
                    `${API_BASE}/claim/${encodeURIComponent(query.toUpperCase())}`,
                    { signal: controller.signal }
                );
                if (res.ok) {
                    const report = await res.json();
                    items = [{
                        type: "report",
                        id: query.toUpperCase(),
                        claim: report.claim,
                        score: report.confidence_score
                    }];
                }
            } else {
                const res = await fetch(
                    `${API_BASE}/search?q=${encodeURIComponent(query)}&limit=5`,
                    { signal: controller.signal }
                );
                if (res.ok) {
                    const payload = await res.json();
                    items = payload.results.slice(0, 5).map((claim) => ({
                        type: "claim",
                        claim: claim
                    }));
                }
            }
        } catch (err) {
            if (err.name !== "AbortError") {
                closePanel();
            }
            return;
        }

        // A newer keystroke superseded this request — drop its results.
        if (activeController !== controller) {
            return;
        }
        activeController = null;

        if (items.length) {
            renderPanel(query, items);
        } else {
            closePanel();
        }
    }

    input.addEventListener("input", () => {
        const query = input.value.trim();
        if (!query) {
            closePanel();
            return;
        }
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => fetchSuggestions(query), 300);
    });

    // One keydown handler: Enter searches (or picks the highlighted
    // suggestion), arrows move the highlight, Escape closes the panel.
    input.addEventListener("keydown", (event) => {
        const options = panel.querySelectorAll(".live-suggestion");

        if (event.key === "Enter") {
            // Always consume the key here (stopImmediatePropagation) so the
            // top-level Enter->searchClaim listener below never double-fires
            // on the home page — a highlighted suggestion must not be
            // overridden by a second navigation to the search page.
            event.stopImmediatePropagation();
            if (!panel.hidden && highlightedIndex >= 0 && options[highlightedIndex]) {
                event.preventDefault();
                options[highlightedIndex].click();
            } else {
                searchClaim();
            }
            return;
        }

        if (panel.hidden || !options.length) {
            return;
        }

        if (event.key === "ArrowDown") {
            event.preventDefault();
            highlightedIndex = (highlightedIndex + 1) % options.length;
            highlight(options);
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            highlightedIndex = (highlightedIndex - 1 + options.length) % options.length;
            highlight(options);
        } else if (event.key === "Escape") {
            closePanel();
            input.blur();
        }
    });

    // Clicking anywhere else closes the suggestions.
    document.addEventListener("click", (event) => {
        if (!searchArea.contains(event.target)) {
            closePanel();
        }
    });
})();

// Enter in the search bar runs the search. Registered AFTER the live-search
// IIFE so it only fires when the IIFE isn't handling the key itself — that
// keeps Enter working on the search-results page's refine bar too (where
// the IIFE bails out early).
document
    .getElementById("claim-input")
    .addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            searchClaim();
        }
    });
