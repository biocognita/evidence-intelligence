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

    const claimId = document
        .getElementById("claim-input")
        .value
        .trim()
        .toUpperCase();

    if (!claimId) {
        return;
    }

    window.location.href = `reportpage.html?claim=${claimId}`;
}