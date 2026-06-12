
import base64
import json
import os
import re
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

try:
    from supabase import create_client
except Exception:
    create_client = None


APP_TITLE = "Ireland’s Flora, Fauna and Birds"
APP_SUBTITLE = "The Majestic Beauty of the Irish Countryside"
DATA_PATH = Path("data/species_seed.csv")
LOCAL_STATE_PATH = Path("data/local_user_state.json")
LOCAL_PHOTOS_PATH = Path("data/local_photos.json")
LOCAL_UPLOADS_DIR = Path("uploads")
PHOTO_BUCKET = "nature-photos"

REQUIRED_SPECIES_COLUMNS = [
    "id",
    "common_name",
    "scientific_name",
    "kingdom_group",
    "category",
    "subcategory",
    "season",
    "habitat",
    "description",
    "edibility",
    "medicinal_uses",
    "warning",
    "conservation_status",
    "image_search",
    "image_url",
]


# ---------- Page setup ----------

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>

        /* Force the app to behave like a website, not like a Streamlit form page */
        header[data-testid="stHeader"] {
            height: 0rem !important;
            background: transparent !important;
            visibility: hidden !important;
        }

        [data-testid="stToolbar"] {
            display: none !important;
        }

        [data-testid="stDecoration"] {
            display: none !important;
        }

        [data-testid="stStatusWidget"] {
            display: none !important;
        }

        .block-container {
            max-width: 100% !important;
            padding-top: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            padding-bottom: 2rem !important;
        }

        .main .block-container {
            padding-top: 0 !important;
        }

        section.main > div {
            padding-top: 0 !important;
        }

        .content-wrap {
            display: block;
            max-width: 1180px;
            margin: 0 auto;
            padding: 0 1rem 2rem 1rem;
        }


        /* Remove any accidental old radio nav if an old browser cache ever renders it */
        .nav-radio,
        div[role="radiogroup"] {
            display: none !important;
        }


        :root {
            --irish-green: #0f5132;
            --leaf-green: #2e8b57;
            --moss: #8fbf45;
            --gold: #f3c85b;
            --cream: #fff9e8;
            --peat: #4a2f22;
            --sky: #dff3ff;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(143,191,69,0.22), transparent 30%),
                radial-gradient(circle at bottom right, rgba(47,132,93,0.18), transparent 35%),
                linear-gradient(180deg, #f8fff3 0%, #fffaf0 100%);
        }


        .hero {
            position: relative;
            min-height: 390px;
            width: calc(100% - 2rem);
            max-width: 1500px;
            margin: 0 auto 1.25rem auto;
            border-radius: 0 0 30px 30px;
            overflow: hidden;
            box-shadow: 0 12px 30px rgba(15, 81, 50, 0.23);
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            border: 0;
        }

        .hero-overlay {
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(8,26,16,0.56) 0%, rgba(8,26,16,0.35) 45%, rgba(8,26,16,0.22) 100%),
                linear-gradient(180deg, rgba(0,0,0,0.10), rgba(0,0,0,0.34));
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 1.2rem;
        }

        .hero-copy {
            max-width: 920px;
        }

        .hero h1 {
            font-size: clamp(2rem, 7vw, 4.6rem);
            line-height: 1.04;
            font-weight: 900;
            margin: 0 0 .45rem 0;
            letter-spacing: -0.03em;
            color: white;
            text-shadow: 0 3px 12px rgba(0,0,0,0.35);
        }

        .hero p {
            font-size: clamp(1rem, 3vw, 1.4rem);
            margin: 0 auto;
            font-style: italic;
            opacity: 0.98;
            color: white;
            text-shadow: 0 2px 10px rgba(0,0,0,0.35);
            max-width: 760px;
        }

        .hero-tags {
            margin-top: 1rem;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: .45rem;
        }

        .hero-tag {
            display: inline-block;
            color: white;
            background: rgba(255,255,255,0.16);
            border: 1px solid rgba(255,255,255,0.32);
            padding: .42rem .75rem;
            border-radius: 999px;
            font-size: .92rem;
            font-weight: 700;
            backdrop-filter: blur(2px);
        }

        .notice {
            border-left: 6px solid var(--gold);
            background: #fff8db;
            color: #4a3600;
            padding: .85rem 1rem;
            border-radius: 15px;
            margin: .8rem 0;
        }

        .safe {
            border-left: 6px solid #0f7b4a;
            background: #eaf8ef;
            color: #153d29;
            padding: .85rem 1rem;
            border-radius: 15px;
            margin: .8rem 0;
        }

        .danger {
            border-left: 6px solid #a22;
            background: #fff0f0;
            color: #631515;
            padding: .85rem 1rem;
            border-radius: 15px;
            margin: .8rem 0;
        }

        .species-card {
            background: rgba(255,255,255,0.86);
            border: 1px solid rgba(15, 81, 50, 0.16);
            border-radius: 24px;
            padding: 1rem;
            margin: .75rem 0;
            box-shadow: 0 6px 18px rgba(50, 80, 45, 0.10);
        }

        .species-title {
            font-size: 1.35rem;
            line-height: 1.15;
            font-weight: 850;
            color: #0f5132;
            margin: 0;
        }

        .latin {
            font-style: italic;
            color: #5b684c;
            margin-bottom: .35rem;
        }

        .badge {
            display: inline-block;
            padding: .22rem .58rem;
            border-radius: 999px;
            background: #edf7e6;
            color: #0f5132;
            font-size: .78rem;
            font-weight: 700;
            margin: .1rem .15rem .1rem 0;
            border: 1px solid rgba(15,81,50,0.16);
        }

        .badge-gold {
            background: #fff2c2;
            color: #624500;
        }

        .badge-red {
            background: #ffe0e0;
            color: #771515;
        }

        .small-muted {
            color: #65745e;
            font-size: .9rem;
        }

        .landscape-card {
            background: rgba(255,255,255,0.92);
            border-radius: 24px;
            overflow: hidden;
            margin: .4rem 0 1rem 0;
            border: 1px solid rgba(15,81,50,.18);
            box-shadow: 0 8px 24px rgba(15,81,50,.13);
        }

        .landscape-card img {
            border-radius: 0;
        }

        .landscape-card-text {
            padding: .85rem 1rem 1rem 1rem;
            background: linear-gradient(180deg, #ffffff 0%, #f0fae9 100%);
        }

        .landscape-card-text h3 {
            color: #0f5132;
            font-size: 1.25rem;
            margin: 0 0 .25rem 0;
            font-weight: 850;
        }

        .landscape-card-text p {
            color: #42513d;
            margin: 0;
            font-size: .95rem;
        }

        .quick-tile {
            background: linear-gradient(135deg, rgba(15,81,50,.95), rgba(143,191,69,.86));
            color: white;
            padding: 1rem;
            min-height: 150px;
            border-radius: 24px;
            box-shadow: 0 8px 24px rgba(15,81,50,.17);
            border: 1px solid rgba(255,255,255,.3);
            margin: .5rem 0;
        }

        .quick-tile h3 {
            margin: 0 0 .4rem 0;
            color: white;
            font-size: 1.25rem;
        }

        .quick-tile p {
            margin: 0;
            color: rgba(255,255,255,.94);
        }

        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .65rem;
            margin: .9rem 0;
        }

        .detail-box {
            background: #f7fff1;
            border: 1px solid rgba(15,81,50,.16);
            border-radius: 18px;
            padding: .75rem;
            color: #213f2d;
        }

        .detail-box strong {
            color: #0f5132;
            display: block;
            margin-bottom: .25rem;
        }

        .detail-box.warning-box {
            background: #fff5ec;
            border-color: rgba(160, 82, 45, .28);
        }

        @media (max-width: 740px) {
            .detail-grid {
                grid-template-columns: 1fr;
            }
        }

        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(15,81,50,.10);
            border-radius: 18px;
            padding: .8rem;
            box-shadow: 0 3px 12px rgba(15,81,50,.08);
        }

        .nav-radio div[role="radiogroup"] {
            gap: .3rem;
        }

        button[kind="primary"] {
            border-radius: 999px !important;
        }

        .stButton button {
            border-radius: 999px;
            border: 1px solid rgba(15,81,50,.25);
        }

        .block-container {
            padding-top: 0.2rem;
        }

        @media (max-width: 740px) {
            .block-container {
                padding-top: 0.2rem;
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }

            .top-nav {
                width: calc(100% + 1.5rem);
                margin: -0.2rem -0.75rem 0.6rem -0.75rem;
                gap: .16rem .35rem;
                padding: .7rem .75rem;
            }

            .top-nav a {
                font-size: .92rem;
                padding: .08rem .22rem;
            }

            .hero {
                min-height: 290px;
                border-radius: 24px;
            }

            .species-card {
                padding: .85rem;
                border-radius: 20px;
            }

            .species-title {
                font-size: 1.18rem;
            }
        }
        
        @media (max-width: 740px) {
            .content-wrap {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }

            .top-nav {
                gap: .45rem .78rem;
                padding: .72rem .75rem;
                overflow-x: auto;
                flex-wrap: nowrap;
                -webkit-overflow-scrolling: touch;
            }

            .top-nav a {
                font-size: .94rem;
            }

            .hero {
                width: 100%;
                min-height: 310px;
                border-radius: 0 0 24px 24px;
                margin-bottom: 1rem;
            }
        }

        
        .top-nav-shell {
            position: sticky;
            top: 0;
            z-index: 999999;
            width: 100%;
            margin: 0;
            padding: 0.55rem 1.1rem;
            background: #446c1f;
            box-shadow: 0 4px 12px rgba(35, 60, 18, 0.18);
        }

        .top-nav-shell + div {
            background: #446c1f;
        }

        /* Style the Streamlit buttons inside the top nav to look like website text links */
        .top-nav-shell ~ div[data-testid="stHorizontalBlock"],
        .top-nav-shell + div[data-testid="stHorizontalBlock"] {
            background: #446c1f;
            margin-top: -0.55rem;
            padding: 0 1.1rem 0.55rem 1.1rem;
            position: sticky;
            top: 0;
            z-index: 999999;
        }

        div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            color: #446c1f !important;
            box-shadow: none !important;
            padding: 0.15rem 0.2rem !important;
            min-height: 1.4rem !important;
            font-weight: 800 !important;
            text-align: left !important;
        }

        div[data-testid="stHorizontalBlock"] button[kind="secondary"] p {
            color: #446c1f !important;
            font-size: 1rem !important;
            font-weight: 800 !important;
            text-align: left !important;
        }

        div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
            text-decoration: underline !important;
            background: rgba(255,255,255,0.08) !important;
        }

        /* Remove any old radio nav if a stale cached page ever tries to render it */
        .nav-radio,
        div[role="radiogroup"] {
            display: none !important;
        }

        
        @media (max-width: 740px) {
            .top-nav-shell {
                padding: 0.5rem 0.65rem;
            }

            .top-nav-shell ~ div[data-testid="stHorizontalBlock"],
            .top-nav-shell + div[data-testid="stHorizontalBlock"] {
                overflow-x: auto;
                flex-wrap: nowrap;
                padding: 0 0.65rem 0.5rem 0.65rem;
            }

            div[data-testid="stHorizontalBlock"] button[kind="secondary"] p {
                font-size: .88rem !important;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )



def render_navbar(current_page: str) -> None:
    pages = [
        ("home", "Home"),
        ("browse", "Browse"),
        ("my-sightings", "My sightings"),
        ("data-setup", "Data setup"),
        ("about", "About"),
    ]

    st.markdown('<div class="top-nav-shell">', unsafe_allow_html=True)
    cols = st.columns([1, 1, 1.35, 1.35, 1], gap="small")

    for col, (slug, label) in zip(cols, pages):
        with col:
            is_active = current_page == slug
            button_label = f"● {label}" if is_active else label
            if st.button(button_label, key=f"nav_{slug}", use_container_width=True):
                st.query_params["page"] = slug
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def hero() -> None:
    hero_image = (
        wiki_image("Killarney National Park")
        or wiki_image("Wicklow Mountains")
        or wiki_image("Irish countryside")
        or placeholder_svg(APP_TITLE, "Landscape")
    )

    st.markdown(
        f"""
        <div class="hero" style="background-image:url('{hero_image}')">
            <div class="hero-overlay">
                <div class="hero-copy">
                    <h1>{APP_TITLE}</h1>
                    <p>{APP_SUBTITLE}</p>
                    <div class="hero-tags">
                        <span class="hero-tag">Woodlands</span>
                        <span class="hero-tag">Waterways</span>
                        <span class="hero-tag">Lakes</span>
                        <span class="hero-tag">Mountains</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Helpers ----------


def normalise_id(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def password_gate() -> bool:
    password = read_secret("APP_PASSWORD", "")
    if not password:
        return True

    if st.session_state.get("password_ok"):
        return True

    st.markdown("### 🔐 Private family field guide")
    entered = st.text_input("Enter app password", type="password")
    if entered and entered == password:
        st.session_state["password_ok"] = True
        st.rerun()
    elif entered:
        st.error("That password is not correct.")
    return False


@st.cache_resource(show_spinner=False)
def get_supabase():
    url = read_secret("SUPABASE_URL", "")
    key = (
        read_secret("SUPABASE_SERVICE_ROLE_KEY", "")
        or read_secret("SUPABASE_ANON_KEY", "")
        or read_secret("SUPABASE_KEY", "")
    )

    if not url or not key or create_client is None:
        return None

    try:
        return create_client(url, key)
    except Exception:
        return None


def supabase_enabled() -> bool:
    return get_supabase() is not None


def ensure_local_files() -> None:
    LOCAL_UPLOADS_DIR.mkdir(exist_ok=True)
    if not LOCAL_STATE_PATH.exists():
        LOCAL_STATE_PATH.write_text("{}", encoding="utf-8")
    if not LOCAL_PHOTOS_PATH.exists():
        LOCAL_PHOTOS_PATH.write_text("[]", encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_seed_species() -> pd.DataFrame:
    if not DATA_PATH.exists():
        st.error("Missing data/species_seed.csv")
        return pd.DataFrame(columns=REQUIRED_SPECIES_COLUMNS)

    df = pd.read_csv(DATA_PATH).fillna("")
    for col in REQUIRED_SPECIES_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df["id"] = df.apply(
        lambda r: r["id"] if str(r["id"]).strip() else normalise_id(r["common_name"]),
        axis=1,
    )
    return df[REQUIRED_SPECIES_COLUMNS].drop_duplicates(subset=["id"]).reset_index(drop=True)


@st.cache_data(ttl=60, show_spinner=False)
def load_species() -> pd.DataFrame:
    seed_df = load_seed_species()
    sb = get_supabase()
    if not sb:
        return seed_df

    try:
        response = sb.table("species").select("*").order("common_name").execute()
        rows = response.data or []
        if not rows:
            return seed_df
        df = pd.DataFrame(rows).fillna("")
        for col in REQUIRED_SPECIES_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[REQUIRED_SPECIES_COLUMNS].drop_duplicates(subset=["id"]).reset_index(drop=True)
    except Exception:
        return seed_df


def load_user_state() -> dict:
    ensure_local_files()
    sb = get_supabase()
    if sb:
        try:
            response = sb.table("species_user_state").select("*").execute()
            rows = response.data or []
            return {
                row["species_id"]: {
                    "spotted": bool(row.get("spotted")),
                    "spotted_at": row.get("spotted_at") or "",
                    "notes": row.get("notes") or "",
                    "updated_at": row.get("updated_at") or "",
                }
                for row in rows
                if row.get("species_id")
            }
        except Exception as exc:
            st.warning(f"Supabase user state could not be loaded, using local fallback. {exc}")

    try:
        return json.loads(LOCAL_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_user_state(species_id: str, spotted: bool, notes: str, spotted_at: str = "") -> None:
    ensure_local_files()
    existing = load_user_state().get(species_id, {})
    if spotted and not spotted_at:
        spotted_at = existing.get("spotted_at") or now_iso()
    if not spotted:
        spotted_at = ""

    row = {
        "species_id": species_id,
        "spotted": bool(spotted),
        "spotted_at": spotted_at,
        "notes": notes or "",
        "updated_at": now_iso(),
    }

    sb = get_supabase()
    if sb:
        try:
            sb.table("species_user_state").upsert(row, on_conflict="species_id").execute()
            st.cache_data.clear()
            return
        except Exception as exc:
            st.error(f"Could not save to Supabase: {exc}")

    try:
        state = json.loads(LOCAL_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    state[species_id] = row
    LOCAL_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_photos(species_id: str | None = None) -> list[dict]:
    ensure_local_files()
    sb = get_supabase()
    if sb:
        try:
            query = sb.table("species_photos").select("*").order("created_at", desc=True)
            if species_id:
                query = query.eq("species_id", species_id)
            return query.execute().data or []
        except Exception as exc:
            st.warning(f"Supabase photos could not be loaded, using local fallback. {exc}")

    try:
        photos = json.loads(LOCAL_PHOTOS_PATH.read_text(encoding="utf-8"))
    except Exception:
        photos = []
    if species_id:
        photos = [p for p in photos if p.get("species_id") == species_id]
    return photos


def add_photo_record(species_id: str, photo_url: str, caption: str, file_name: str) -> None:
    row = {
        "species_id": species_id,
        "photo_url": photo_url,
        "caption": caption or "",
        "file_name": file_name or "",
        "created_at": now_iso(),
    }

    sb = get_supabase()
    if sb:
        try:
            sb.table("species_photos").insert(row).execute()
            st.cache_data.clear()
            return
        except Exception as exc:
            st.error(f"Photo was uploaded, but the photo record could not be saved: {exc}")

    photos = load_photos()
    row["id"] = str(int(time.time() * 1000))
    photos.insert(0, row)
    LOCAL_PHOTOS_PATH.write_text(json.dumps(photos, indent=2), encoding="utf-8")


def upload_photo(species_id: str, uploaded_file, caption: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", uploaded_file.name)
    path = f"{species_id}/{int(time.time())}_{safe_name}"
    content = uploaded_file.getvalue()

    sb = get_supabase()
    if sb:
        try:
            sb.storage.from_(PHOTO_BUCKET).upload(
                path,
                content,
                file_options={
                    "content-type": uploaded_file.type or "application/octet-stream",
                    "upsert": "true",
                },
            )
            public_url = sb.storage.from_(PHOTO_BUCKET).get_public_url(path)
            add_photo_record(species_id, public_url, caption, uploaded_file.name)
            return public_url
        except Exception as exc:
            st.error(
                "Supabase photo upload failed. Check that the storage bucket exists "
                f"and policies are enabled. Details: {exc}"
            )

    LOCAL_UPLOADS_DIR.mkdir(exist_ok=True)
    local_path = LOCAL_UPLOADS_DIR / path.replace("/", "_")
    local_path.write_bytes(content)
    add_photo_record(species_id, str(local_path), caption, uploaded_file.name)
    return str(local_path)


def image_from_file(path_or_url: str):
    if not path_or_url:
        return None
    if path_or_url.startswith("http"):
        return path_or_url
    path = Path(path_or_url)
    if path.exists():
        return str(path)
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def wiki_image(search_name: str) -> str:
    if not search_name:
        return ""
    headers = {
        "User-Agent": "IrishNatureTracker/1.0 (educational Streamlit app)"
    }
    candidates = []
    for item in [search_name, search_name.replace("Irish ", ""), search_name.replace("Common ", "")]:
        item = item.strip()
        if item and item not in candidates:
            candidates.append(item)

    for candidate in candidates:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(candidate.replace(' ', '_'))}"
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code != 200:
                continue
            data = res.json()
            thumb = data.get("thumbnail", {}) or {}
            original = data.get("originalimage", {}) or {}
            image = original.get("source") or thumb.get("source") or ""
            if image:
                return image
        except Exception:
            continue
    return ""


def placeholder_svg(label: str, group: str = "") -> str:
    emoji = "🍃"
    if "bird" in group.lower() or "avian" in group.lower():
        emoji = "🐦"
    elif "fauna" in group.lower():
        emoji = "🦊"
    elif "flora" in group.lower():
        emoji = "🌿"

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="620">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop stop-color="#0f5132" offset="0"/>
          <stop stop-color="#8fbf45" offset="1"/>
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#g)"/>
      <circle cx="150" cy="120" r="90" fill="rgba(255,255,255,0.18)"/>
      <circle cx="760" cy="500" r="150" fill="rgba(255,255,255,0.16)"/>
      <text x="50%" y="42%" text-anchor="middle" font-size="110">{emoji}</text>
      <text x="50%" y="58%" text-anchor="middle" fill="white" font-size="46" font-family="Arial" font-weight="700">{label[:30]}</text>
      <text x="50%" y="68%" text-anchor="middle" fill="rgba(255,255,255,0.88)" font-size="28" font-family="Arial">Irish Nature Tracker</text>
    </svg>
    """
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


def species_image(row: pd.Series) -> str:
    explicit = str(row.get("image_url", "") or "").strip()
    if explicit:
        return explicit

    image_search = str(row.get("image_search", "") or "").strip()
    scientific = str(row.get("scientific_name", "") or "").strip()
    common = str(row.get("common_name", "") or "").strip()

    for candidate in [image_search, scientific, common]:
        img = wiki_image(candidate)
        if img:
            return img

    return placeholder_svg(common, str(row.get("kingdom_group", "")))


def edibility_badge_class(value: str) -> str:
    v = (value or "").lower()
    if any(word in v for word in ["poison", "toxic", "deadly", "not edible"]):
        return "badge-red"
    if any(word in v for word in ["caution", "limited", "expert", "n/a"]):
        return "badge-gold"
    return ""


def filter_df(df: pd.DataFrame, state: dict) -> pd.DataFrame:
    search = st.text_input("Search by name, habitat, description, season, use, or warning", placeholder="Try: woodland, edible, winter, coast, medicinal...")
    col1, col2 = st.columns(2)
    with col1:
        groups = ["All"] + sorted(df["kingdom_group"].dropna().unique().tolist())
        group = st.selectbox("Group", groups)
    with col2:
        categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
        category = st.selectbox("Category", categories)

    col3, col4 = st.columns(2)
    with col3:
        edibility = st.selectbox(
            "Edibility",
            ["All", "Edible", "Caution", "Not edible / toxic", "N/A or unknown"],
        )
    with col4:
        spotted_filter = st.selectbox("Spotted status", ["All", "Spotted", "Not spotted"])

    result = df.copy()

    if group != "All":
        result = result[result["kingdom_group"] == group]
    if category != "All":
        result = result[result["category"] == category]

    if edibility != "All":
        lower = result["edibility"].fillna("").str.lower()
        if edibility == "Edible":
            result = result[lower.str.contains("edible") & ~lower.str.contains("not|poison|toxic|caution", regex=True)]
        elif edibility == "Caution":
            result = result[lower.str.contains("caution|expert|limited", regex=True)]
        elif edibility == "Not edible / toxic":
            result = result[lower.str.contains("not edible|toxic|poison|deadly", regex=True)]
        else:
            result = result[lower.str.contains("n/a|unknown|not foraged", regex=True)]

    if spotted_filter != "All":
        spotted_ids = {sid for sid, row in state.items() if row.get("spotted")}
        if spotted_filter == "Spotted":
            result = result[result["id"].isin(spotted_ids)]
        else:
            result = result[~result["id"].isin(spotted_ids)]

    if search:
        q = search.strip().lower()
        haystack_cols = [
            "common_name",
            "scientific_name",
            "kingdom_group",
            "category",
            "subcategory",
            "season",
            "habitat",
            "description",
            "edibility",
            "medicinal_uses",
            "warning",
            "conservation_status",
        ]
        mask = pd.Series(False, index=result.index)
        for col in haystack_cols:
            mask |= result[col].fillna("").str.lower().str.contains(re.escape(q), na=False)
        result = result[mask]

    return result.reset_index(drop=True)


def sync_seed_to_supabase(df: pd.DataFrame) -> tuple[bool, str]:
    sb = get_supabase()
    if not sb:
        return False, "Supabase is not configured."

    records = df.fillna("").to_dict(orient="records")
    try:
        # Upsert in small batches to avoid request limits.
        for i in range(0, len(records), 50):
            sb.table("species").upsert(records[i:i+50], on_conflict="id").execute()
        st.cache_data.clear()
        return True, f"Synced {len(records)} species records to Supabase."
    except Exception as exc:
        return False, f"Could not sync species data: {exc}"


def import_species_csv(uploaded_file) -> tuple[bool, str]:
    try:
        imported = pd.read_csv(uploaded_file).fillna("")
    except Exception as exc:
        return False, f"Could not read CSV: {exc}"

    missing = [c for c in REQUIRED_SPECIES_COLUMNS if c not in imported.columns]
    if missing:
        return False, f"CSV is missing columns: {', '.join(missing)}"

    imported["id"] = imported.apply(
        lambda r: r["id"] if str(r["id"]).strip() else normalise_id(r["common_name"]),
        axis=1,
    )

    sb = get_supabase()
    if not sb:
        return False, "CSV import into the live app requires Supabase. Without Supabase, edit data/species_seed.csv in GitHub."

    try:
        records = imported[REQUIRED_SPECIES_COLUMNS].to_dict(orient="records")
        for i in range(0, len(records), 50):
            sb.table("species").upsert(records[i:i+50], on_conflict="id").execute()
        st.cache_data.clear()
        return True, f"Imported {len(records)} species records."
    except Exception as exc:
        return False, f"Could not import CSV into Supabase: {exc}"


# ---------- UI Components ----------



def species_detail(row: pd.Series, state: dict) -> None:
    species_id = row["id"]
    current = state.get(species_id, {})
    spotted_default = bool(current.get("spotted", False))
    notes_default = current.get("notes", "")

    st.markdown('<div class="species-card">', unsafe_allow_html=True)
    img_col, text_col = st.columns([1, 1.55], vertical_alignment="top")

    with img_col:
        st.image(species_image(row), width="stretch")
        if spotted_default:
            st.success("✅ Spotted")
        else:
            st.caption("Not yet spotted")

    with text_col:
        st.markdown(f"<p class='species-title'>{row['common_name']}</p>", unsafe_allow_html=True)
        if row["scientific_name"]:
            st.markdown(f"<div class='latin'>{row['scientific_name']}</div>", unsafe_allow_html=True)

        ed_class = edibility_badge_class(row["edibility"])
        badges = [
            (row["kingdom_group"], ""),
            (row["category"], ""),
            (row["subcategory"], ""),
            (row["season"], "badge-gold"),
            (row["edibility"], ed_class),
        ]
        html_badges = "".join(
            f"<span class='badge {klass}'>{text}</span>"
            for text, klass in badges
            if str(text).strip()
        )
        st.markdown(html_badges, unsafe_allow_html=True)

        st.write(row["description"])

        st.markdown(
            f"""
            <div class="detail-grid">
                <div class="detail-box"><strong>Habitat</strong>{row['habitat'] or 'Not specified'}</div>
                <div class="detail-box"><strong>Season / when seen</strong>{row['season'] or 'Not specified'}</div>
                <div class="detail-box"><strong>Edible / foraging</strong>{row['edibility'] or 'Not specified'}</div>
                <div class="detail-box"><strong>Medicinal / traditional uses</strong>{row['medicinal_uses'] or 'Not specified'}</div>
                <div class="detail-box warning-box"><strong>Warnings</strong>{row['warning'] or 'None listed'}</div>
                <div class="detail-box"><strong>Conservation / status</strong>{row['conservation_status'] or 'Not specified'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    col_a, col_b = st.columns([1, 2])
    with col_a:
        spotted = st.checkbox("I have spotted this", value=spotted_default, key=f"spot_{species_id}")
    with col_b:
        spotted_at = current.get("spotted_at") or ""
        if spotted_at:
            try:
                dt = datetime.fromisoformat(spotted_at.replace("Z", "+00:00"))
                st.caption(f"First recorded: {dt.strftime('%d %b %Y, %H:%M')}")
            except Exception:
                st.caption(f"First recorded: {spotted_at}")

    notes = st.text_area(
        "My notes",
        value=notes_default,
        key=f"notes_{species_id}",
        placeholder="Where did you see it? What was the weather like? Any details to remember?",
        height=110,
    )

    save_col, upload_col = st.columns([1, 1])
    with save_col:
        if st.button("Save notes / spotted status", key=f"save_{species_id}", type="primary"):
            save_user_state(species_id, spotted, notes)
            st.success("Saved.")
            st.rerun()

    with upload_col:
        with st.expander("Upload a photo"):
            uploaded = st.file_uploader(
                "Choose a photo from your gallery",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"upload_{species_id}",
            )
            caption = st.text_input("Photo caption", key=f"caption_{species_id}", placeholder="Optional")
            if uploaded and st.button("Save photo", key=f"save_photo_{species_id}"):
                with st.spinner("Saving photo..."):
                    url = upload_photo(species_id, uploaded, caption)
                    if url:
                        save_user_state(species_id, True, notes)
                        st.success("Photo saved and item marked as spotted.")
                        st.rerun()

    photos = load_photos(species_id)
    if photos:
        st.markdown("**My uploaded photos**")
        cols = st.columns(3)
        for i, p in enumerate(photos[:6]):
            with cols[i % 3]:
                img = image_from_file(p.get("photo_url", ""))
                if img:
                    st.image(img, width="stretch")
                if p.get("caption"):
                    st.caption(p["caption"])

    st.markdown("</div>", unsafe_allow_html=True)


def home_page(df: pd.DataFrame, state: dict) -> None:
    st.markdown(
        """
        <div class="safe">
        A colourful mobile field guide for Irish wildflowers, trees, shrubs, mammals, insects, freshwater life,
        coastal species, and Ireland’s resident and migratory birds — inspired by Ireland’s woodlands, waterways,
        lakes and mountains.
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown("### Explore by living world")
    tile_cols = st.columns(4)
    tiles = [
        ("🌿 Flora", "Wildflowers, grasses, mosses, seaweeds and bog plants."),
        ("🌳 Trees & Shrubs", "Native trees, hedgerows, woodland species and berries."),
        ("🦊 Animals", "Mammals, amphibians, reptiles, fish and marine life."),
        ("🦋 Insects & Invertebrates", "Butterflies, bees, beetles, dragonflies, spiders and shoreline life."),
    ]
    for i, (name, text) in enumerate(tiles):
        with tile_cols[i]:
            st.markdown(f"<div class='quick-tile'><h3>{name}</h3><p>{text}</p></div>", unsafe_allow_html=True)

    spotted_count = sum(1 for item in state.values() if item.get("spotted"))
    flora_count = int((df["kingdom_group"] == "Flora").sum())
    fauna_count = int((df["kingdom_group"] == "Fauna").sum())
    avian_count = int((df["kingdom_group"] == "Birds").sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Species in guide", len(df))
    m2.metric("Flora", flora_count)
    m3.metric("Fauna", fauna_count)
    m4.metric("Birds", avian_count)

    st.metric("Your spotted records", spotted_count)

    st.markdown(
        """
        <div class="danger">
        <strong>Foraging and medical safety:</strong> this app is educational only. Never eat wild plants,
        fungi, berries, or seaweeds unless confirmed by an expert field guide and a competent local identifier.
        Do not use traditional medicinal information as medical advice.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("What you can record")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🌿 Flora")
        st.write("Wildflowers, trees, shrubs, grasses, mosses, bog plants, coastal plants, seaweeds and edible cautions.")
    with col2:
        st.markdown("### 🦊 Fauna")
        st.write("Mammals, amphibians, reptiles, insects, spiders, molluscs, freshwater fish, marine life and shoreline wildlife.")
    with col3:
        st.markdown("### 🐦 Birds")
        st.write("Resident birds, summer visitors, winter visitors, seabirds, raptors, ducks, geese and waders.")

    st.subheader("Seasonal suggestions")
    month = datetime.now().month
    if month in [3, 4, 5]:
        terms = ["Spring", "Mar", "Apr", "May"]
    elif month in [6, 7, 8]:
        terms = ["Summer", "Jun", "Jul", "Aug"]
    elif month in [9, 10, 11]:
        terms = ["Autumn", "Sep", "Oct", "Nov"]
    else:
        terms = ["Winter", "Dec", "Jan", "Feb"]

    season_mask = df["season"].fillna("").str.contains("|".join(terms), case=False, regex=True)
    suggestions = df[season_mask].head(6)
    if suggestions.empty:
        suggestions = df.sample(min(6, len(df)), random_state=2)

    for _, row in suggestions.iterrows():
        with st.expander(f"{row['common_name']} — {row['category']}"):
            species_detail(row, state)


def browse_page(df: pd.DataFrame, state: dict) -> None:
    st.subheader("Browse the field guide")
    result = filter_df(df, state)

    st.caption(f"Showing {len(result)} of {len(df)} records.")
    if result.empty:
        st.warning("No records match those filters.")
        return

    page_size = st.selectbox("Records per page", [5, 10, 20, 50], index=3)
    total_pages = max(1, (len(result) + page_size - 1) // page_size)
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    start = (page - 1) * page_size
    end = start + page_size

    for _, row in result.iloc[start:end].iterrows():
        with st.expander(f"{'✅ ' if state.get(row['id'], {}).get('spotted') else ''}{row['common_name']} — {row['category']}"):
            species_detail(row, state)


def sightings_page(df: pd.DataFrame, state: dict) -> None:
    st.subheader("My sightings and notes")
    spotted_ids = [sid for sid, data in state.items() if data.get("spotted")]
    spotted_df = df[df["id"].isin(spotted_ids)].copy()

    if spotted_df.empty:
        st.info("You have not marked anything as spotted yet.")
    else:
        st.success(f"You have recorded {len(spotted_df)} spotted items.")
        for _, row in spotted_df.sort_values(["kingdom_group", "common_name"]).iterrows():
            data = state.get(row["id"], {})
            with st.expander(f"✅ {row['common_name']} — {row['category']}"):
                st.markdown(f"**Scientific name:** *{row['scientific_name']}*")
                st.markdown(f"**Habitat:** {row['habitat']}")
                if data.get("notes"):
                    st.markdown(f"**Your notes:** {data['notes']}")
                if data.get("spotted_at"):
                    st.caption(f"Recorded: {data['spotted_at']}")

    st.divider()
    st.subheader("My photo gallery")
    photos = load_photos()
    if not photos:
        st.info("No photos uploaded yet.")
        return

    species_lookup = df.set_index("id")["common_name"].to_dict()
    cols = st.columns(2)
    for i, photo in enumerate(photos):
        with cols[i % 2]:
            img = image_from_file(photo.get("photo_url", ""))
            if img:
                st.image(img, width="stretch")
            st.markdown(f"**{species_lookup.get(photo.get('species_id'), photo.get('species_id'))}**")
            if photo.get("caption"):
                st.caption(photo["caption"])
            if photo.get("created_at"):
                st.caption(photo["created_at"])


def data_page(df: pd.DataFrame) -> None:
    st.subheader("Data and Supabase setup")

    if supabase_enabled():
        st.success("Supabase is configured.")
    else:
        st.warning(
            "Supabase is not configured. The app will run, but notes/photos/spotted items will only use local fallback storage. "
            "For Streamlit Cloud and mobile use, configure Supabase secrets."
        )

    st.markdown("### Seed the live species table")
    st.write(
        "The app includes a starter CSV. When Supabase is configured, press this once to copy the starter records into your Supabase species table."
    )
    if st.button("Sync starter species data to Supabase", type="primary"):
        ok, msg = sync_seed_to_supabase(load_seed_species())
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    st.markdown("### Import more species later")
    st.write(
        "Upload a CSV with the same columns as the starter file. This lets you expand the app over time."
    )
    uploaded_csv = st.file_uploader("Upload species CSV", type=["csv"])
    if uploaded_csv and st.button("Import CSV into Supabase"):
        ok, msg = import_species_csv(uploaded_csv)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    st.download_button(
        "Download current starter CSV template",
        data=load_seed_species().to_csv(index=False).encode("utf-8"),
        file_name="irish_nature_species_template.csv",
        mime="text/csv",
    )

    with st.expander("Species table preview"):
        st.dataframe(df, width="stretch", hide_index=True)


def about_page() -> None:
    st.subheader("About this app")
    st.write(
        "This field guide is designed for family walks, school nature projects, countryside trips, and personal wildlife records."
    )

    st.markdown(
        """
        **Built-in features**
        - Irish flora, fauna, and bird guide
        - Resident and migratory bird categories
        - Search and filters
        - Spotted checklist
        - Personal notes
        - Photo uploads from mobile gallery
        - Supabase database and storage support
        - Local fallback mode for testing
        - CSV import for future expansion
        """
    )

    st.markdown(
        """
        <div class="notice">
        Species information is a practical educational summary, not a replacement for expert botanical,
        ecological, medical, or foraging guidance. Image lookup uses Wikipedia/Wikimedia where available,
        with a local illustrated placeholder if no image is found.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Main ----------


def main() -> None:
    inject_css()

    raw_page = st.query_params.get("page", "home")
    if isinstance(raw_page, list):
        raw_page = raw_page[0] if raw_page else "home"

    page = str(raw_page).strip().lower() or "home"
    valid_pages = {"home", "browse", "my-sightings", "data-setup", "about"}
    if page not in valid_pages:
        page = "home"

    render_navbar(page)
    hero()

    if not password_gate():
        return

    df = load_species()
    state = load_user_state()

    if not df.empty:
        df = df.sort_values(["kingdom_group", "category", "common_name"]).reset_index(drop=True)

    st.markdown('<main class="content-wrap">', unsafe_allow_html=True)

    if page == "home":
        home_page(df, state)
    elif page == "browse":
        browse_page(df, state)
    elif page == "my-sightings":
        sightings_page(df, state)
    elif page == "data-setup":
        data_page(df)
    else:
        about_page()

    st.markdown("</main>", unsafe_allow_html=True)


if __name__ == "__main__":

    main()
