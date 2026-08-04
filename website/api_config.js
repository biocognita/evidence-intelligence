// API configuration for the Evidence Intelligence frontend.
//
// The HTML pages are a static shell — they always talk to the Python
// (Flask) backend, which serves the real data from Google Sheets.
// This is the ONE place the backend address lives, so you never have to
// hunt through the pages to change it.
//
// If you run app.py on a different port (see the PORT environment
// variable in script/app.py), update API_BASE to match.
const API_BASE = "http://localhost:5001";
