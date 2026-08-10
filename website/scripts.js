document
    .getElementById("search-button")
    .addEventListener("click", searchClaim);

document
    .getElementById("claim-input")
    .addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            searchClaim();
        }
    });

// Fade the About Us / Methodology cards in as they scroll into view.
// Uses IntersectionObserver; respects prefers-reduced-motion (handled in
// CSS, which forces .reveal to stay fully visible there).
(function initScrollReveal() {
    const revealEls = document.querySelectorAll(".reveal");
    if (!revealEls.length) {
        return; // not the home page — nothing to reveal
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
})();

function searchClaim() {

    const query = document
        .getElementById("claim-input")
        .value
        .trim();

    if (!query) {
        return;
    }

    const columnSelect = document.getElementById("search-column");
    const column = columnSelect ? columnSelect.value : "Claim";

    // A claim ID (e.g. C0001 or c0001) jumps straight to its report.
    if (/^c[0-9]{4}$/i.test(query)) {
        window.location.href = `reportpage.html?claim=${query.toUpperCase()}`;
        return;
    }

    // Anything else is free-text search against the selected column.
    const params = new URLSearchParams({ q: query, col: column });
    window.location.href = `searchpage.html?${params.toString()}`;
}
