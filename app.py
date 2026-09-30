import html
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from eligibility_engine import find_scholarships


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ScholarSync",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Looks for the dataset next to this file (your Scholarsync folder).
# The first file that exists in this list is used.
BASE_DIR = Path(__file__).resolve().parent
_CANDIDATES = [
    "scholarships_final_v2.csv",
    "Scholarships_final.csv",
    "scholarships_standardized.csv",
]
DATA_PATH = next(
    (BASE_DIR / name for name in _CANDIDATES if (BASE_DIR / name).exists()),
    BASE_DIR / _CANDIDATES[-1],
)

if not DATA_PATH.exists():
    st.error(f"Dataset not found. Put one of these next to app.py: {', '.join(_CANDIDATES)}")
    st.stop()

NAV = [
    "Home",
    "Find Scholarships",
    "Explore",
    "Deadline Radar",
    "Saved",
    "Documents Checklist",
    "About",
]
PASTELS = ["lav", "mint", "peach", "butter", "sky", "pink"]


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    data.columns = data.columns.astype(str).str.strip()
    return data


df = load_data()


# ============================================================
# HELPERS
# ============================================================

def h(markup: str) -> str:
    """Flatten HTML so Markdown never mistakes indented lines for code blocks."""
    return " ".join(line.strip() for line in markup.splitlines() if line.strip())


def ui(markup: str):
    st.markdown(h(markup), unsafe_allow_html=True)


def esc(value, fallback="Not specified") -> str:
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    if text.lower() in ("", "nan", "none", "nat"):
        return fallback
    return html.escape(text)


def card(key: str):
    """A container that the CSS turns into a sticker card."""
    try:
        return st.container(key=key)
    except TypeError:
        return st.container(border=True)


def link_btn(label: str, url: str, key: str):
    try:
        st.link_button(label, url, key=key)
    except TypeError:
        st.link_button(label, url)


# ---------- official links (display only, never used for eligibility) ----------

# If True, a scholarship with no `official_website` falls back to the existing
# `official_url` column (real links already in your CSV). Set to False to use
# only the new `official_website` column.
USE_OFFICIAL_URL_FALLBACK = True

_NOT_A_URL = {"", "nan", "none", "null", "nat", "n/a", "na", "-", "not specified"}


def is_valid_url(url) -> bool:
    """True only for a real http(s) URL. Never raises."""
    try:
        if url is None or (not isinstance(url, str) and pd.isna(url)):
            return False
        text = str(url).strip()
        if text.lower() in _NOT_A_URL or any(ch.isspace() for ch in text):
            return False
        parsed = urlparse(text)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname) and "." in parsed.hostname
    except Exception:
        return False


def _link_lookup(data: pd.DataFrame) -> dict:
    """scholarship_id -> row values, so links can be found even if the result rows lack them."""
    if "scholarship_id" not in data.columns:
        return {}
    return {str(k).strip(): rec for k, rec in zip(data["scholarship_id"], data.to_dict("records"))}


LINK_LOOKUP = _link_lookup(df)


def get_scholarship_links(row):
    """Return (official_website, application_link); each is a valid URL or None."""
    sources = [row]
    try:
        rec = LINK_LOOKUP.get(str(row.get("scholarship_id")).strip())
        if rec is not None:
            sources.append(rec)
    except Exception:
        pass

    def first_valid(column):
        for source in sources:
            try:
                value = source.get(column)
            except Exception:
                continue
            if is_valid_url(value):
                return str(value).strip()
        return None

    website = first_valid("official_website")
    if website is None and USE_OFFICIAL_URL_FALLBACK:
        website = first_valid("official_url")

    return website, first_valid("application_link")


def render_link_buttons(row, key_prefix: str):
    """Official website / Apply buttons for one scholarship. Missing links are skipped."""
    website, apply_url = get_scholarship_links(row)

    # Same URL for both? Show a single Apply button instead of two identical ones.
    if website and apply_url and website.rstrip("/") == apply_url.rstrip("/"):
        website = None

    if website and apply_url:
        col_site, col_apply = st.columns(2)
        with col_site:
            link_btn("View Official Website", website, key=f"{key_prefix}_site")
        with col_apply:
            link_btn("Apply / Register \u2192", apply_url, key=f"{key_prefix}_apply")
    elif website:
        link_btn("View Official Website", website, key=f"{key_prefix}_site")
        st.caption("Application link not available.")
    elif apply_url:
        link_btn("Apply / Register \u2192", apply_url, key=f"{key_prefix}_apply")
    else:
        st.caption("Official application link not available.")


def go_find():
    st.session_state["page"] = "Find Scholarships"


def go(page_name: str):
    """Navigate to another page (used as a button callback)."""
    st.session_state["page"] = page_name


# ---------- saved scholarships (kept in session state) ----------

SID_COL = "scholarship_id" if "scholarship_id" in df.columns else "scholarship_name"


def sid_of(row) -> str:
    return str(row.get(SID_COL)).strip()


def toggle_save(sid: str):
    saved = st.session_state.setdefault("saved", set())
    saved.symmetric_difference_update({sid})


def save_btn(row, key: str):
    is_saved = sid_of(row) in st.session_state.get("saved", set())
    st.button(
        "\u2605 Saved" if is_saved else "\u2606 Save",
        key=key,
        on_click=toggle_save,
        args=(sid_of(row),),
    )


def page_header(kicker: str, title: str, sub: str = ""):
    ui(
        f"""
        <div class="page-head">
            <div class="kicker">{kicker}</div>
            <div class="page-title">{title}</div>
            <div class="page-sub">{sub}</div>
        </div>
        """
    )


# ============================================================
# CUSTOM CSS
# ============================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Caveat:wght@600;700&display=swap');

:root {
    --ink: #2A2540;
    --ink-soft: #6B6585;
    --paper: #FBF9FF;
    --white: #FFFFFF;
    --lav: #D9CEFF;
    --lav-d: #B9A6FF;
    --mint: #C4F0DD;
    --mint-d: #5FBF98;
    --peach: #FFD3C4;
    --peach-d: #F2907A;
    --butter: #FFF0AE;
    --sky: #C5E5FF;
    --pink: #FFCDE5;
    --grey: #E9E6F0;
}

/* ---------- base ---------- */
.stApp {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: var(--ink);
    background-color: var(--paper);
    background-image: radial-gradient(#DDD3F5 1.3px, transparent 1.3px);
    background-size: 24px 24px;
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 5rem; }
.stApp p, .stApp label { color: var(--ink); }
.stApp a { color: var(--ink); }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
    background: var(--lav);
    border-right: 2.5px solid var(--ink);
}
section[data-testid="stSidebar"] > div { padding-top: 1rem; }
.logo {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 800;
    font-size: 27px;
    letter-spacing: -1px;
    display: inline-block;
    background: var(--white);
    border: 2.5px solid var(--ink);
    border-radius: 14px;
    padding: 4px 14px;
    box-shadow: 4px 4px 0 var(--ink);
    transform: rotate(-2deg);
}
.side-tag { font-family: 'Caveat', cursive; font-size: 21px; margin: 14px 0 6px 4px; line-height: 1.1; }
.side-stat {
    background: var(--butter);
    border: 2.5px solid var(--ink);
    border-radius: 18px;
    padding: 14px 16px;
    box-shadow: 4px 4px 0 var(--ink);
    transform: rotate(1.5deg);
    margin-top: 26px;
}
.side-stat .num { font-family: 'Bricolage Grotesque', sans-serif; font-size: 34px; font-weight: 800; line-height: 1; }
.side-stat .lbl { font-size: 13px; font-weight: 600; margin-top: 4px; }

/* ---------- radio as pills ---------- */
div[role="radiogroup"] { gap: 10px; flex-wrap: wrap; }
div[role="radiogroup"] label {
    background: var(--white);
    border: 2px solid var(--ink);
    border-radius: 999px;
    padding: 7px 18px;
    box-shadow: 3px 3px 0 var(--ink);
    cursor: pointer;
    transition: transform .12s, box-shadow .12s, background .12s;
}
div[role="radiogroup"] label > div:first-child { display: none; }
div[role="radiogroup"] label p { font-weight: 700; font-size: 14px; margin: 0; }
div[role="radiogroup"] label:hover { transform: translate(-1px, -1px); box-shadow: 4px 4px 0 var(--ink); }
div[role="radiogroup"] label:has(input:checked) { background: var(--lav-d); box-shadow: 1px 1px 0 var(--ink); transform: translate(2px, 2px); }
section[data-testid="stSidebar"] div[role="radiogroup"] label { width: 100%; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) { background: var(--peach); }

/* ---------- inputs ---------- */
div[data-baseweb="select"] > div,
div[data-baseweb="input"],
div[data-baseweb="base-input"] {
    background: var(--white) !important;
    border: 2px solid var(--ink) !important;
    border-radius: 14px !important;
    min-height: 46px;
}
div[data-baseweb="input"] input,
div[data-baseweb="select"] input { color: var(--ink) !important; font-weight: 500; }
.stApp label p { font-weight: 700; font-size: 14px; }

/* ---------- buttons ---------- */
.stButton > button,
a[data-testid^="stBaseLinkButton"] {
    border: 2.5px solid var(--ink) !important;
    border-radius: 14px !important;
    min-height: 48px;
    font-weight: 700;
    background: var(--white) !important;
    color: var(--ink) !important;
    box-shadow: 4px 4px 0 var(--ink);
    transition: transform .12s, box-shadow .12s;
}
.stButton > button p, a[data-testid^="stBaseLinkButton"] p { color: var(--ink) !important; font-weight: 700; }
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"] { background: var(--lav-d) !important; }
.stButton > button:hover,
a[data-testid^="stBaseLinkButton"]:hover { transform: translate(-1px, -1px); box-shadow: 6px 6px 0 var(--ink); }
.stButton > button:active,
a[data-testid^="stBaseLinkButton"]:active { transform: translate(3px, 3px); box-shadow: 1px 1px 0 var(--ink); }

/* ---------- sticker cards (st.container with key) ---------- */
div[class*="st-key-card-"] {
    background: var(--white);
    border: 2.5px solid var(--ink);
    border-radius: 24px;
    padding: 24px 26px;
    box-shadow: 6px 6px 0 var(--ink);
    margin-bottom: 18px;
}

/* ---------- expander ---------- */
div[data-testid="stExpander"] details {
    border: 2px solid var(--ink);
    border-radius: 14px;
    background: var(--paper);
}
div[data-testid="stExpander"] summary p { font-weight: 700; }

/* ---------- page header ---------- */
.page-head { margin-bottom: 22px; }
.kicker { font-family: 'Caveat', cursive; font-size: 26px; color: var(--ink-soft); line-height: 1; }
.page-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 800;
    font-size: 44px;
    letter-spacing: -1.8px;
    line-height: 1.05;
    margin-top: 4px;
}
.page-sub { color: var(--ink-soft); font-size: 16px; margin-top: 10px; max-width: 620px; line-height: 1.6; }

/* ---------- hero ---------- */
.hero {
    display: flex; flex-wrap: wrap; gap: 36px; align-items: center; justify-content: space-between;
    background: var(--white);
    border: 2.5px solid var(--ink);
    border-radius: 32px;
    padding: 46px 48px;
    box-shadow: 8px 8px 0 var(--ink);
    overflow: hidden;
}
.hero-left { flex: 1 1 380px; max-width: 620px; }
.hero-hand { font-family: 'Caveat', cursive; font-size: 28px; color: var(--ink-soft); line-height: 1; }
.hero-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 800;
    font-size: 58px;
    line-height: 1;
    letter-spacing: -2.6px;
    margin-top: 10px;
}
.hero-desc { font-size: 17px; line-height: 1.7; color: var(--ink-soft); margin-top: 20px; max-width: 540px; }
.tag-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.tag {
    display: inline-block;
    border: 2px solid var(--ink);
    border-radius: 999px;
    padding: 4px 13px;
    font-size: 13px;
    font-weight: 700;
    color: var(--ink);
}
.bg-lav { background: var(--lav); } .bg-mint { background: var(--mint); } .bg-peach { background: var(--peach); }
.bg-butter { background: var(--butter); } .bg-sky { background: var(--sky); } .bg-pink { background: var(--pink); }
.bg-grey { background: var(--grey); }

/* planner sticky notes */
.hero-right { flex: 0 1 330px; position: relative; min-height: 330px; width: 100%; }
.sticky {
    position: absolute;
    border: 2.5px solid var(--ink);
    border-radius: 6px 6px 22px 6px;
    box-shadow: 5px 5px 0 var(--ink);
    padding: 18px 20px;
}
.sticky.one { background: var(--butter); width: 270px; top: 0; right: 30px; transform: rotate(3deg); z-index: 2; }
.sticky.two { background: var(--pink); width: 220px; bottom: 0; left: 0; transform: rotate(-4deg); z-index: 3; }
.sticky.three { background: var(--sky); width: 130px; bottom: 26px; right: 0; transform: rotate(6deg); z-index: 1; text-align: center; }
.sticky .head { font-family: 'Caveat', cursive; font-size: 27px; line-height: 1; margin-bottom: 10px; }
.todo { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 14px; margin-bottom: 9px; }
.box { width: 18px; height: 18px; border: 2px solid var(--ink); border-radius: 5px; background: var(--white); flex: none;
       display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; }
.box.done { background: var(--mint-d); }
.sticky .big { font-family: 'Bricolage Grotesque', sans-serif; font-size: 40px; font-weight: 800; line-height: 1; }
.sticky .small { font-size: 12px; font-weight: 700; margin-top: 4px; }
.sticky .hand { font-family: 'Caveat', cursive; font-size: 22px; line-height: 1.15; }

/* ---------- stat tiles ---------- */
.tile {
    border: 2.5px solid var(--ink);
    border-radius: 20px;
    padding: 18px 20px;
    box-shadow: 4px 4px 0 var(--ink);
    height: 100%;
}
.tile .lbl { font-size: 13px; font-weight: 700; }
.tile .val { font-family: 'Bricolage Grotesque', sans-serif; font-size: 34px; font-weight: 800; letter-spacing: -1px; margin-top: 4px; line-height: 1.1; }

/* ---------- section heading ---------- */
.sec-title { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 34px; letter-spacing: -1.4px; margin: 30px 0 4px; }
.sec-sub { color: var(--ink-soft); margin-bottom: 18px; }

/* ---------- how it works ---------- */
.step-num {
    width: 38px; height: 38px; border-radius: 50%;
    border: 2.5px solid var(--ink);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 17px;
    margin-bottom: 14px;
}
.step-title { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 21px; letter-spacing: -0.5px; }
.step-desc { color: var(--ink-soft); font-size: 14.5px; line-height: 1.6; margin-top: 6px; }
.step-card { border: 2.5px solid var(--ink); border-radius: 22px; padding: 24px; box-shadow: 5px 5px 0 var(--ink); height: 100%; }

/* ---------- note strip ---------- */
.note-strip {
    display: flex; gap: 14px; align-items: center;
    background: var(--butter);
    border: 2.5px dashed var(--ink);
    border-radius: 18px;
    padding: 16px 22px;
    margin-top: 26px;
    font-weight: 600;
    line-height: 1.5;
}
.note-strip .hand { font-family: 'Caveat', cursive; font-size: 26px; flex: none; }

/* ---------- match card ---------- */
.m-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; flex-wrap: wrap; }
.m-name { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 23px; letter-spacing: -0.7px; line-height: 1.2; }
.m-meta { color: var(--ink-soft); font-size: 13.5px; margin-top: 5px; font-weight: 500; }
.badge { display: inline-block; border: 2px solid var(--ink); border-radius: 999px; padding: 5px 13px; font-size: 12.5px; font-weight: 800; white-space: nowrap; }
.meter { display: flex; align-items: center; gap: 12px; margin: 16px 0 12px; }
.meter .segs { display: flex; gap: 5px; }
.meter .seg { width: 26px; height: 10px; border: 2px solid var(--ink); border-radius: 99px; background: var(--white); }
.meter .seg.on { background: var(--mint-d); }
.meter .txt { font-size: 13px; font-weight: 700; }
.chips { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; margin-bottom: 16px; }
.chip { border: 2px solid var(--ink); border-radius: 12px; padding: 8px 12px; font-size: 13.5px; font-weight: 700; display: flex; gap: 9px; align-items: center; }
.chip.ok { background: var(--mint); }
.chip.unk { background: var(--butter); }
.chip .mark { width: 20px; height: 20px; border-radius: 50%; border: 2px solid var(--ink); background: var(--white);
              display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; flex: none; }
.info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 14px; }
.info-box { background: var(--paper); border: 2px solid var(--ink); border-radius: 14px; padding: 12px 16px; }
.info-box .lbl { font-family: 'Caveat', cursive; font-size: 21px; line-height: 1; color: var(--ink-soft); }
.info-box .val { font-size: 14.5px; font-weight: 600; margin-top: 4px; line-height: 1.5; }
.reason-key { font-weight: 800; }
.reason-val { color: var(--ink-soft); margin-bottom: 10px; }

/* ---------- explore card ---------- */
.e-name { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 20px; letter-spacing: -0.5px; line-height: 1.25; margin-top: 12px; }
.e-row { font-size: 14px; margin-top: 10px; line-height: 1.5; }
.e-row b { font-weight: 800; }

/* ---------- deadline radar ---------- */
.month-head { font-family: 'Caveat', cursive; font-size: 34px; margin: 26px 0 8px 4px; line-height: 1; }
.dl { display: flex; gap: 18px; align-items: center; background: var(--white); border: 2.5px solid var(--ink);
      border-radius: 20px; padding: 14px 20px 14px 14px; box-shadow: 4px 4px 0 var(--ink); margin-bottom: 14px; }
.dl-date { flex: none; width: 74px; border: 2.5px solid var(--ink); border-radius: 14px; text-align: center; padding: 8px 0 7px; }
.dl-date .d { font-family: 'Bricolage Grotesque', sans-serif; font-size: 28px; font-weight: 800; line-height: 1; }
.dl-date .m { font-size: 12px; font-weight: 800; margin-top: 3px; }
.dl-body { flex: 1; min-width: 0; }
.dl-name { font-family: 'Bricolage Grotesque', sans-serif; font-size: 18px; font-weight: 700; letter-spacing: -0.4px; line-height: 1.25; }
.dl-meta { color: var(--ink-soft); font-size: 13.5px; margin-top: 4px; }

@media (max-width: 720px) {
    .hero { padding: 28px 24px; }
    .hero-title { font-size: 40px; letter-spacing: -1.6px; }
    .page-title { font-size: 34px; }
    .hero-right { min-height: 300px; }
    .dl { flex-wrap: wrap; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    ui('<div class="logo">ScholarSync</div>')
    ui('<div class="side-tag">find money for your degree</div>')

    st.radio("Navigate", NAV, key="page", label_visibility="collapsed")

    ui(
        f"""
        <div class="side-stat">
            <div class="num">{len(df)}</div>
            <div class="lbl">scholarships in the database</div>
        </div>
        """
    )

    ui(
        """
        <div class="side-tag" style="margin-top:22px;">
            always check the official site before you apply.
        </div>
        """
    )

page = st.session_state.get("page", "Home")


# ============================================================
# HOME
# ============================================================

if page == "Home":

    ui(
        """
        <div class="hero">

            <div class="hero-left">
                <div class="hero-hand">scholarship discovery, reimagined</div>
                <div class="hero-title">Scholarships shouldn't be this hard to find.</div>
                <div class="hero-desc">
                    ScholarSync compares your student profile with scholarship
                    opportunities and explains exactly why each one shows up in
                    your shortlist.
                </div>
                <div class="tag-row">
                    <span class="tag bg-lav">Structured matching</span>
                    <span class="tag bg-mint">Transparent reasoning</span>
                    <span class="tag bg-peach">Official sources</span>
                </div>
            </div>

            <div class="hero-right">

                <div class="sticky one">
                    <div class="head">to-do today</div>
                    <div class="todo"><span class="box done">&#10003;</span>Build your profile</div>
                    <div class="todo"><span class="box"></span>Check your matches</div>
                    <div class="todo"><span class="box"></span>Verify on the official site</div>
                </div>

                <div class="sticky two">
                    <div class="hand">see why a scholarship matched, not just that it did</div>
                </div>

                <div class="sticky three">
                    <div class="big">6</div>
                    <div class="small">eligibility checks</div>
                </div>

            </div>

        </div>
        """
    )

    st.write("")

    st.button(
        "Find scholarships for me",
        type="primary",
        use_container_width=True,
        on_click=go_find,
    )

    # Quick-jump buttons
    q1, q2, q3, q4 = st.columns(4)
    q1.button("Explore all", use_container_width=True, on_click=go, args=("Explore",))
    q2.button("Deadline Radar", use_container_width=True, on_click=go, args=("Deadline Radar",))
    q3.button("My saved", use_container_width=True, on_click=go, args=("Saved",))
    q4.button("Documents checklist", use_container_width=True, on_click=go, args=("Documents Checklist",))

    st.write("")

    stats = [
        ("Scholarships", len(df), "lav"),
        ("Eligibility factors", 6, "mint"),
        ("Deadline tracking", "Yes", "butter"),
        ("Official sources", "Linked", "peach"),
    ]

    for col, (label, value, colour) in zip(st.columns(4), stats):
        with col:
            ui(
                f"""
                <div class="tile bg-{colour}">
                    <div class="lbl">{label}</div>
                    <div class="val">{value}</div>
                </div>
                """
            )

    ui('<div class="sec-title">From profile to shortlist in three steps.</div>')
    ui('<div class="sec-sub">No sign-up, no long forms. Just the basics.</div>')

    steps = [
        ("1", "Build your profile",
         "Tell us your education level, course, state, category, gender and family income.", "sky"),
        ("2", "Understand your matches",
         "The matching engine evaluates the eligibility information available for each scholarship.", "pink"),
        ("3", "Verify before applying",
         "See what matched, what is still unknown, and where to check the official requirements.", "mint"),
    ]

    for col, (num, title, desc, colour) in zip(st.columns(3), steps):
        with col:
            ui(
                f"""
                <div class="step-card bg-{colour}">
                    <div class="step-num" style="background:#fff;">{num}</div>
                    <div class="step-title">{title}</div>
                    <div class="step-desc">{desc}</div>
                </div>
                """
            )

    ui(
        """
        <div class="note-strip">
            <span class="hand">heads up</span>
            <span>
                ScholarSync identifies potentially suitable opportunities from the
                available data. Always verify the official scholarship guidelines
                before applying.
            </span>
        </div>
        """
    )


# ============================================================
# FIND SCHOLARSHIPS
# ============================================================

elif page == "Find Scholarships":

    page_header(
        "step 1: your profile",
        "Tell us a little about yourself.",
        "We use these details to screen the scholarship database. Nothing is stored.",
    )

    with card("card-profile"):

        col1, col2 = st.columns(2)

        with col1:

            education = st.selectbox(
                "Education level",
                [
                    "School",
                    "Intermediate (Class 11-12)",
                    "Diploma",
                    "Undergraduate",
                    "Postgraduate",
                    "PhD",
                ],
            )

            course = st.text_input(
                "Course / field",
                placeholder="B.Tech, MBBS, B.Com, MBA...",
            )

            state = st.selectbox(
                "State / UT",
                sorted(df["state"].dropna().astype(str).unique()),
            )

        with col2:

            category = st.selectbox(
                "Category",
                ["General", "SC", "ST", "OBC", "EWS", "Minority", "PWD"],
            )

            gender = st.selectbox("Gender", ["Male", "Female", "Other"])

            income = st.number_input(
                "Annual family income (₹)",
                min_value=0,
                value=200000,
                step=10000,
            )

    find_button = st.button(
        "Find my scholarships",
        type="primary",
        use_container_width=True,
    )

    if find_button:

        with st.spinner("Checking scholarship requirements..."):

            results = find_scholarships(
                education=education,
                course=course,
                state=state,
                category=category,
                gender=gender,
                income=income,
            )

        st.session_state["results"] = results

        st.session_state["student_profile"] = {
            "education": education,
            "course": course,
            "state": state,
            "category": category,
            "gender": gender,
            "income": income,
        }

    # ========================================================
    # RESULTS
    # ========================================================

    if "results" in st.session_state:

        results = st.session_state["results"]

        st.write("")

        if results.empty:

            ui(
                """
                <div class="note-strip" style="background:var(--peach);">
                    <span class="hand">no luck yet</span>
                    <span>
                        No scholarship could be identified without an explicit
                        eligibility conflict. Try changing your category, state
                        or income and search again.
                    </span>
                </div>
                """
            )

        else:

            potentially = int((results["status"] == "Potentially Eligible").sum())
            verification = int((results["status"] == "Needs Verification").sum())

            page_header(
                "step 2: your shortlist",
                f"{len(results)} opportunities found.",
                "Ordered by explicit matches and how much eligibility information is missing.",
            )

            t1, t2, t3 = st.columns(3)

            with t1:
                ui(
                    f"""
                    <div class="tile bg-lav">
                        <div class="lbl">Total matches</div>
                        <div class="val">{len(results)}</div>
                    </div>
                    """
                )
            with t2:
                ui(
                    f"""
                    <div class="tile bg-mint">
                        <div class="lbl">Potentially eligible</div>
                        <div class="val">{potentially}</div>
                    </div>
                    """
                )
            with t3:
                ui(
                    f"""
                    <div class="tile bg-butter">
                        <div class="lbl">Need verification</div>
                        <div class="val">{verification}</div>
                    </div>
                    """
                )

            st.write("")

            show = st.radio(
                "Show",
                ["All", "Potentially eligible", "Needs verification"],
                horizontal=True,
                key="result_filter",
                label_visibility="collapsed",
            )

            shown = results
            if show == "Potentially eligible":
                shown = results[results["status"] == "Potentially Eligible"]
            elif show == "Needs verification":
                shown = results[results["status"] == "Needs Verification"]

            st.write("")

            if shown.empty:
                ui(
                    """
                    <div class="note-strip">
                        <span class="hand">nothing here</span>
                        <span>No scholarships in this group. Switch the filter above.</span>
                    </div>
                    """
                )

            for i, (_, row) in enumerate(shown.iterrows()):

                if row["status"] == "Potentially Eligible":
                    badge = '<span class="badge bg-mint">Potentially eligible</span>'
                else:
                    badge = '<span class="badge bg-butter">Needs verification</span>'

                criteria = [
                    ("Education", row["checks"]["education"]),
                    ("State", row["checks"]["state"]),
                    ("Category", row["checks"]["category"]),
                    ("Gender", row["checks"]["gender"]),
                    ("Income", row["checks"]["income"]),
                    ("Course", row["checks"]["course"]),
                ]

                matched = sum(1 for _, r in criteria if r == "match")

                segs = "".join(
                    f'<span class="seg {"on" if n < matched else ""}"></span>'
                    for n in range(len(criteria))
                )

                chips = "".join(
                    (
                        f'<div class="chip ok"><span class="mark">&#10003;</span>{label}</div>'
                        if result == "match"
                        else f'<div class="chip unk"><span class="mark">?</span>{label}</div>'
                    )
                    for label, result in criteria
                )

                with card(f"card-match-{i}"):

                    ui(
                        f"""
                        <div class="m-head">
                            <div>
                                <div class="m-name">{esc(row["scholarship_name"])}</div>
                                <div class="m-meta">{esc(row["scheme_type"])}</div>
                            </div>
                            <div>{badge}</div>
                        </div>

                        <div class="meter">
                            <div class="segs">{segs}</div>
                            <div class="txt">{matched} of {len(criteria)} checks matched</div>
                        </div>

                        <div class="chips">{chips}</div>

                        <div class="info-grid">
                            <div class="info-box">
                                <div class="lbl">benefit</div>
                                <div class="val">{esc(row["benefit"])}</div>
                            </div>
                            <div class="info-box">
                                <div class="lbl">closing date</div>
                                <div class="val">{esc(row["closing_date"])}</div>
                            </div>
                        </div>
                        """
                    )

                    with st.expander("Why did this scholarship appear?"):

                        for key, reason in row["reasons"].items():
                            ui(
                                f"""
                                <div class="reason-key">{esc(str(key).title())}</div>
                                <div class="reason-val">{esc(reason)}</div>
                                """
                            )

                    render_link_buttons(row, key_prefix=f"match_{i}")
                    save_btn(row, key=f"save_match_{i}")


# ============================================================
# EXPLORE
# ============================================================

elif page == "Explore":

    page_header(
        "browse everything",
        "Explore scholarships.",
        "Browse the whole database without creating a profile.",
    )

    with card("card-filters"):

        search = st.text_input(
            "Search",
            placeholder="Search by scholarship name, ministry, state...",
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            education_filter = st.selectbox(
                "Education",
                ["All"] + sorted(df["education_level"].dropna().astype(str).unique()),
            )

        with col2:
            state_filter = st.selectbox(
                "State",
                ["All"] + sorted(df["state"].dropna().astype(str).unique()),
            )

        with col3:
            category_filter = st.selectbox(
                "Category",
                ["All"] + sorted(df["category"].dropna().astype(str).unique()),
            )

    filtered = df.copy()

    if search:
        search_text = search.lower()
        mask = (
            filtered.astype(str)
            .apply(lambda column: column.str.lower().str.contains(search_text, na=False, regex=False))
            .any(axis=1)
        )
        filtered = filtered[mask]

    if education_filter != "All":
        filtered = filtered[filtered["education_level"] == education_filter]

    if state_filter != "All":
        filtered = filtered[filtered["state"] == state_filter]

    if category_filter != "All":
        filtered = filtered[filtered["category"] == category_filter]

    filtered = filtered.reset_index(drop=True)

    ui(
        f"""
        <div style="margin:4px 0 18px;">
            <span class="tag bg-butter">{len(filtered)} scholarships</span>
        </div>
        """
    )

    if filtered.empty:

        ui(
            """
            <div class="note-strip" style="background:var(--peach);">
                <span class="hand">no results</span>
                <span>Nothing matches these filters. Clear the search or set a filter back to All.</span>
            </div>
            """
        )

    else:

        limit = st.session_state.get("explore_limit", 20)
        visible = filtered.head(limit)

        for start in range(0, len(visible), 2):

            cols = st.columns(2)

            for offset in range(2):

                idx = start + offset

                if idx >= len(visible):
                    break

                row = visible.iloc[idx]
                colour = PASTELS[idx % len(PASTELS)]

                with cols[offset]:

                    with card(f"card-explore-{idx}"):

                        ui(
                            f"""
                            <span class="tag bg-{colour}">{esc(row["scheme_type"])}</span>
                            <div class="e-name">{esc(row["scholarship_name"])}</div>
                            <div class="e-row"><b>Education:</b> {esc(row["education_level"])}</div>
                            <div class="e-row"><b>State:</b> {esc(row["state"])}</div>
                            <div class="e-row" style="margin-bottom:14px;"><b>Benefit:</b> {esc(row["benefit"])}</div>
                            """
                        )

                        url = str(row["official_url"])

                        if url.startswith("http"):
                            link_btn("View official source", url, key=f"view_{idx}")

                        save_btn(row, key=f"save_explore_{idx}")

        if len(filtered) > limit:

            def show_more():
                st.session_state["explore_limit"] = st.session_state.get("explore_limit", 20) + 20

            st.button(
                f"Show more ({len(filtered) - limit} left)",
                use_container_width=True,
                on_click=show_more,
            )


# ============================================================
# DEADLINE RADAR
# ============================================================

elif page == "Deadline Radar":

    page_header(
        "plan your applications",
        "Deadline Radar.",
        "Every scholarship with a closing date, sorted so the urgent ones come first.",
    )

    deadline_data = df.copy()

    deadline_data["closing_date"] = pd.to_datetime(
        deadline_data["closing_date"], errors="coerce"
    )

    deadline_data = deadline_data.dropna(subset=["closing_date"])

    today = pd.Timestamp(datetime.now().date())

    deadline_data["days_left"] = (deadline_data["closing_date"] - today).dt.days

    upcoming_n = int((deadline_data["days_left"] >= 0).sum())
    soon_n = int(deadline_data["days_left"].between(0, 30).sum())
    closed_n = int((deadline_data["days_left"] < 0).sum())

    t1, t2, t3 = st.columns(3)

    with t1:
        ui(f'<div class="tile bg-mint"><div class="lbl">Still open</div><div class="val">{upcoming_n}</div></div>')
    with t2:
        ui(f'<div class="tile bg-peach"><div class="lbl">Closing in 30 days</div><div class="val">{soon_n}</div></div>')
    with t3:
        ui(f'<div class="tile bg-grey"><div class="lbl">Already closed</div><div class="val">{closed_n}</div></div>')

    st.write("")

    view = st.radio(
        "View",
        ["Upcoming", "Closing soon", "Closed", "All"],
        horizontal=True,
        key="deadline_view",
        label_visibility="collapsed",
    )

    if view == "Upcoming":
        rows = deadline_data[deadline_data["days_left"] >= 0].sort_values("closing_date")
    elif view == "Closing soon":
        rows = deadline_data[deadline_data["days_left"].between(0, 30)].sort_values("closing_date")
    elif view == "Closed":
        rows = deadline_data[deadline_data["days_left"] < 0].sort_values("closing_date", ascending=False)
    else:
        rows = deadline_data.sort_values("closing_date")

    if rows.empty:

        ui(
            """
            <div class="note-strip">
                <span class="hand">all clear</span>
                <span>No scholarships in this view. Try another tab above.</span>
            </div>
            """
        )

    last_month = None

    for _, row in rows.iterrows():

        date = row["closing_date"]
        days = int(row["days_left"])

        month_key = (date.year, date.month)

        if month_key != last_month:
            ui(f'<div class="month-head">{date.strftime("%B %Y").lower()}</div>')
            last_month = month_key

        if days < 0:
            colour, chip_text = "grey", "Closed"
        elif days == 0:
            colour, chip_text = "peach", "Closes today"
        elif days <= 14:
            colour, chip_text = "peach", f"{days} day{'s' if days != 1 else ''} left"
        elif days <= 45:
            colour, chip_text = "butter", f"{days} days left"
        else:
            colour, chip_text = "mint", f"{days} days left"

        ui(
            f"""
            <div class="dl">
                <div class="dl-date bg-{colour}">
                    <div class="d">{date.strftime("%d")}</div>
                    <div class="m">{date.strftime("%b").lower()} {date.strftime("%Y")}</div>
                </div>
                <div class="dl-body">
                    <div class="dl-name">{esc(row["scholarship_name"])}</div>
                    <div class="dl-meta">{esc(row["state"])} &nbsp;|&nbsp; {esc(row["scheme_type"])}</div>
                </div>
                <span class="badge bg-{colour}">{chip_text}</span>
            </div>
            """
        )


# ============================================================
# SAVED
# ============================================================

elif page == "Saved":

    page_header(
        "your bookmarks",
        "Saved scholarships.",
        "Saved items last until you close or refresh the tab.",
    )

    saved = st.session_state.get("saved", set())
    saved_rows = df[df[SID_COL].astype(str).str.strip().isin(saved)]

    if saved_rows.empty:

        ui(
            """
            <div class="note-strip">
                <span class="hand">empty</span>
                <span>Nothing saved yet. Tap \u2606 Save on any scholarship.</span>
            </div>
            """
        )

    else:

        st.button(
            "Clear all saved",
            on_click=lambda: st.session_state.update(saved=set()),
        )

        st.write("")

        for i, (_, row) in enumerate(saved_rows.iterrows()):

            with card(f"card-saved-{i}"):

                ui(
                    f"""
                    <div class="m-name">{esc(row["scholarship_name"])}</div>
                    <div class="m-meta">{esc(row["scheme_type"])} | {esc(row["state"])}</div>
                    <div class="e-row"><b>Benefit:</b> {esc(row["benefit"])}</div>
                    <div class="e-row" style="margin-bottom:14px;"><b>Closing:</b> {esc(row["closing_date"])}</div>
                    """
                )

                render_link_buttons(row, key_prefix=f"saved_{i}")
                save_btn(row, key=f"unsave_{i}")


# ============================================================
# DOCUMENTS CHECKLIST
# ============================================================

elif page == "Documents Checklist":

    page_header(
        "get ready",
        "Documents checklist.",
        "Common documents needed for Indian scholarships. Tick what you have.",
    )

    docs = [
        "Aadhaar card",
        "Income certificate",
        "Caste / category certificate",
        "Domicile certificate",
        "Previous marksheets",
        "Admission / fee receipt",
        "Bank passbook (Aadhaar-linked)",
        "Passport-size photo",
        "Disability certificate (if PWD)",
    ]

    with card("card-docs"):
        done = sum(st.checkbox(d, key=f"doc_{n}") for n, d in enumerate(docs))

    st.progress(done / len(docs), text=f"{done} of {len(docs)} ready")

    ui(
        """
        <div class="note-strip">
            <span class="hand">tip</span>
            <span>Requirements differ by scheme. Confirm the exact list on the official website.</span>
        </div>
        """
    )


# ============================================================
# ABOUT
# ============================================================

elif page == "About":

    page_header(
        "about",
        "How ScholarSync works.",
        "Matching is rule-based and transparent.",
    )

    with card("card-about"):
        st.markdown(
            "- Checks 6 factors: education, state, category, gender, income, course\n"
            "- Unknown criteria are marked **Needs verification**, never assumed\n"
            "- Data comes from the CSV; links are for reference only\n"
            "- Always confirm on the official website before applying"
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    f"ScholarSync · {len(df)} scholarship records · "
    "Always verify eligibility on the official scholarship source."
)