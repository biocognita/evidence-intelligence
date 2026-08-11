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

function searchClaim() {

    const query = document
        .getElementById("claim-input")
        .value
        .trim();

    if (!query) {
        return;
    }

    // A claim ID (e.g. C0001 or c0001) jumps straight to its report.
    if (/^c[0-9]{4}$/i.test(query)) {
        window.location.href = `reportpage.html?claim=${query.toUpperCase()}`;
        return;
    }

    // Anything else is a free-text search across ALL fields (claim,
    // claim ID, intervention, outcome, population).
    const params = new URLSearchParams({ q: query });
    window.location.href = `searchpage.html?${params.toString()}`;
}
