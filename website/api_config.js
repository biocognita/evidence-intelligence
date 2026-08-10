// API configuration for the Evidence Intelligence frontend.
//
// The HTML pages are a static shell — they always talk to the Python
// (Flask) backend, which serves the real data from Google Sheets.
//
// The backend serves these very pages itself, so when the site is opened
// over http(s) (locally via app.py, or on Render), the API lives on the
// SAME origin — use a relative URL so it works without any hardcoded host.
//
// The only exception is opening a page straight from disk (file://), where
// there is no origin — fall back to the local dev server on localhost:5001.
const API_BASE = window.location.protocol === "file:"
    ? "http://localhost:5001"
    : "";
