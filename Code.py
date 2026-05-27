"""
study_rpg.py — Full Study RPG in one file.
Run with: streamlit run study_rpg.py
"""

import streamlit as st
import json, os, time, random, math
from datetime import datetime, date

# ============================================================
#  SAVE / LOAD
# ============================================================

DATA_FILE    = "study_rpg_player.json"
HISTORY_FILE = "study_rpg_history.json"

DEFAULT_PLAYER = {
    "name": "Scholar",
    "xp": 0,
    "level": 1,
    "streak": 0,
    "last_study_date": None,
    "total_study_minutes": 0,
    "sessions_completed": 0,
    "theme": "cozy_cafe",
    "unlocked_themes": ["cozy_cafe"],
    "unlocked_titles": ["Student"],
    "active_title": "Student",
    "achievements": [],
    "daily_quests": [],
    "quests_reset_date": None,
    "sound_enabled": True,
}

def load_player():
    if not os.path.exists(DATA_FILE):
        save_player(DEFAULT_PLAYER.copy())
        return DEFAULT_PLAYER.copy()
    with open(DATA_FILE) as f:
        data = json.load(f)
    for k, v in DEFAULT_PLAYER.items():
        if k not in data:
            data[k] = v
    return data

def save_player(p):
    with open(DATA_FILE, "w") as f:
        json.dump(p, f, indent=2)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        h = {"sessions": []}
        with open(HISTORY_FILE, "w") as f:
            json.dump(h, f)
        return h
    with open(HISTORY_FILE) as f:
        return json.load(f)

def save_history(h):
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)

# ============================================================
#  GAME LOGIC
# ============================================================

def calculate_xp_gain(minutes):
    base = minutes * 2
    if minutes >= 90: return base + 100
    if minutes >= 60: return base + 50
    if minutes >= 45: return base + 20
    return base

def add_xp(p, xp):
    old_level = p["level"]
    p["xp"] += xp
    p["level"] = max(1, p["xp"] // 100)
    leveled_up = p["level"] > old_level
    if leveled_up:
        p = apply_level_rewards(p, p["level"])
    return p, leveled_up, p["level"]

def apply_level_rewards(p, level):
    REWARDS = {
        2:  {"theme": "dark_academia", "title": "Night Owl"},
        5:  {"theme": "cyberpunk",     "title": "Digital Monk"},
        8:  {"theme": "retro_arcade",  "title": "Knight of the Pomodoro"},
        12: {"theme": "aquarium",      "title": "Deep Focus Diver"},
        18: {"theme": "space_station", "title": "Academic Weapon"},
        25: {"title": "Sleep-Deprived Scholar"},
        35: {"title": "Legendary Nerd"},
    }
    if level in REWARDS:
        r = REWARDS[level]
        if "theme" in r and r["theme"] not in p["unlocked_themes"]:
            p["unlocked_themes"].append(r["theme"])
        if "title" in r and r["title"] not in p["unlocked_titles"]:
            p["unlocked_titles"].append(r["title"])
    return p

def update_streak(p):
    today = str(date.today())
    last = p.get("last_study_date")
    broken = False
    if last is None:
        p["streak"] = 1
    elif last == today:
        pass
    else:
        delta = (date.today() - date.fromisoformat(last)).days
        if delta == 1:
            p["streak"] += 1
        else:
            broken = True
            p["streak"] = 1
    p["last_study_date"] = today
    return p, broken

def add_session(p, minutes, xp):
    h = load_history()
    h["sessions"].append({"date": str(datetime.now()), "minutes": minutes, "xp_gained": xp})
    save_history(h)
    p["sessions_completed"] += 1
    p["total_study_minutes"] += minutes
    return p

def get_or_refresh_quests(p):
    today = str(date.today())
    if p.get("quests_reset_date") != today or not p.get("daily_quests"):
        pool = [
            {"id":"q1","text":"Complete 2 study sessions","type":"sessions","target":2,"xp":50,"done":False},
            {"id":"q2","text":"Study for 60 minutes total","type":"minutes","target":60,"xp":60,"done":False},
            {"id":"q3","text":"Crush one 45-min session","type":"long_session","target":45,"xp":40,"done":False},
            {"id":"q4","text":"Drink water during your break 💧","type":"wellness","target":1,"xp":20,"done":False},
            {"id":"q5","text":"Complete 3 sessions in a row","type":"sessions","target":3,"xp":80,"done":False},
            {"id":"q6","text":"Study for 90 minutes total","type":"minutes","target":90,"xp":100,"done":False},
            {"id":"q7","text":"Start a session before noon 🌅","type":"morning","target":1,"xp":30,"done":False},
            {"id":"q8","text":"Complete 1 Pomodoro session","type":"sessions","target":1,"xp":25,"done":False},
        ]
        p["daily_quests"] = random.sample(pool, 3)
        p["quests_reset_date"] = today
        save_player(p)
    return p

ACHIEVEMENTS = {
    "first_session": {"name":"First Steps",       "desc":"Complete your very first session",  "icon":"🌱"},
    "streak_3":      {"name":"On a Roll",          "desc":"3-day study streak",                "icon":"🔥"},
    "streak_7":      {"name":"Weekly Warrior",     "desc":"7-day study streak",                "icon":"⚔️"},
    "level_5":       {"name":"Rising Scholar",     "desc":"Reach level 5",                     "icon":"⭐"},
    "level_10":      {"name":"Dedicated",          "desc":"Reach level 10",                    "icon":"💫"},
    "hours_10":      {"name":"Time Wizard",        "desc":"Study for 10 hours total",          "icon":"⏰"},
    "night_owl":     {"name":"Night Owl",          "desc":"Study after midnight",              "icon":"🦉"},
    "marathon":      {"name":"Marathon Runner",    "desc":"Complete a 90-min session",         "icon":"🏃"},
}

def check_achievements(p):
    earned = p.get("achievements", [])
    new = []
    hour = datetime.now().hour
    checks = [
        ("first_session", p.get("sessions_completed",0) >= 1),
        ("streak_3",      p.get("streak",0) >= 3),
        ("streak_7",      p.get("streak",0) >= 7),
        ("level_5",       p.get("level",1) >= 5),
        ("level_10",      p.get("level",1) >= 10),
        ("hours_10",      p.get("total_study_minutes",0) >= 600),
        ("night_owl",     hour >= 23 or hour <= 4),
        ("marathon",      p.get("total_study_minutes",0) >= 90),
    ]
    for key, cond in checks:
        if cond and key not in earned:
            earned.append(key)
            new.append(key)
    p["achievements"] = earned
    return p, new

def get_level_title(level):
    if level < 3:  return "Humble Learner"
    if level < 6:  return "Aspiring Scholar"
    if level < 10: return "Focused Mind"
    if level < 15: return "Seasoned Student"
    if level < 20: return "Academic Weapon"
    if level < 30: return "Legendary Nerd"
    return "Transcendent Brain"

# ============================================================
#  MASCOT
# ============================================================

MASCOT_EMOJI = {
    "happy":   "🦊",
    "sleepy":  "🦥",
    "proud":   "🦁",
    "sad":     "🐧",
    "chaotic": "🦇",
}

MASCOT_MOOD_LABEL = {
    "happy":   "Hyped up!",
    "sleepy":  "Half-asleep...",
    "proud":   "Absolutely feral with pride",
    "sad":     "A little lost",
    "chaotic": "MIDNIGHT CHAOS MODE",
}

MASCOT_LINES = {
    "happy": [
        "You studied! I shall compose a ballad in your honor. 🎵",
        "This is the best day of my life. Again. Like every time you open this app.",
        "We are UNSTOPPABLE. Well, you are. I'm a mascot. But emotionally? Unstoppable.",
        "Session complete! The ancient scholars weep tears of joy. ✨",
        "You absolute LEGEND. Have you considered a trophy? I'm considering a trophy.",
    ],
    "sleepy": [
        "...zzzz... oh! You're here. I definitely wasn't sleeping. I was meditating.",
        "I've been waiting. Not dramatically or anything. Just... waiting. For hours.",
        "Good morning? Good evening? Time is a concept I've abandoned.",
        "Oh thank goodness. I was starting to think you'd forgotten about me. (I knew you hadn't.)",
        "The library misses you. I miss you. Even the study table seems lonely.",
    ],
    "proud": [
        "A 7-day streak?! I'm going to need a moment. *wipes tear* This is beautiful.",
        "You are BUILT different. The other mascots wish they had someone like you.",
        "Look at you. Just LOOK at you. A true scholar in their natural habitat.",
        "I've been telling everyone about you. They don't believe me. I will make them believers.",
        "One more session and we ascend. I can feel it. ✨",
    ],
    "sad": [
        "Day 3 of no studying. I've started naming the furniture. This is Chairles.",
        "We haven't focused in days. I'm starting to see ghosts. They're also procrastinating.",
        "I'm fine. This is fine. *is not fine* Come back. Please. For Chairles.",
        "The quests are gathering dust. The XP bar weeps. I weep. We all weep.",
        "No pressure, but the streak counter is now literally crying. Just thought you should know.",
    ],
    "chaotic": [
        "It's past midnight. We're studying at MIDNIGHT. This is either genius or chaos. Both.",
        "The witching hour of academia! The brain fog is a feature now, not a bug!",
        "Sleep? Sleep is for the WEEKDAY VERSION of us. Tonight we TRANSCEND.",
        "Your circadian rhythm called. I told it we were busy. It seemed upset.",
        "Midnight session unlocked! Achievement: 'What Even Is Sleep'. Wear it proudly. 🌙",
    ],
}

def get_mascot_mood(p):
    last  = p.get("last_study_date")
    today = str(date.today())
    hour  = datetime.now().hour
    days_since = (date.today() - date.fromisoformat(last)).days if last else 99
    if hour >= 23 or hour <= 4:  return "chaotic"
    if days_since >= 3:          return "sad"
    if p.get("streak", 0) >= 7: return "proud"
    if last == today:            return "happy"
    return "sleepy"

def mascot_line(mood):
    return random.choice(MASCOT_LINES.get(mood, MASCOT_LINES["happy"]))

# ============================================================
#  THEMES  (colors + CSS)
# ============================================================

THEMES = {
    "cozy_cafe": {
        "name": "☕ Cozy Café", "emoji": "☕",
        "desc": "Warm, soft, like studying in your favorite corner booth.",
        "unlock_level": 1,
        "font_display": "Playfair Display", "font_body": "Lora",
        "c": {
            "bg":      "#1a1008", "bg2": "#2d1f0e",
            "card":    "rgba(255,220,170,.08)", "border": "rgba(255,200,130,.2)",
            "accent":  "#e8a87c", "accent2": "#d4876a",
            "txt":     "#f5e6d3", "txt2": "#c4a882",
            "xpbar":   "linear-gradient(90deg,#e8a87c,#d4875a)",
            "glow":    "rgba(232,168,124,.3)",
            "btn":     "linear-gradient(135deg,#c47a45,#a85c30)",
            "pbg":     "rgba(255,200,130,.15)",
            "pattern": "radial-gradient(ellipse at 20% 50%,rgba(180,100,40,.15) 0%,transparent 60%),radial-gradient(ellipse at 80% 20%,rgba(100,60,20,.2) 0%,transparent 50%)",
        },
    },
    "dark_academia": {
        "name": "📚 Dark Academia", "emoji": "📚",
        "desc": "Candlelight, old books, and the smell of ambition.",
        "unlock_level": 2,
        "font_display": "Cinzel", "font_body": "EB Garamond",
        "c": {
            "bg":      "#0e0c0a", "bg2": "#1a1510",
            "card":    "rgba(180,150,100,.07)", "border": "rgba(160,130,80,.25)",
            "accent":  "#c9a84c", "accent2": "#8b6914",
            "txt":     "#e8dcc8", "txt2": "#a89060",
            "xpbar":   "linear-gradient(90deg,#c9a84c,#8b6914)",
            "glow":    "rgba(201,168,76,.25)",
            "btn":     "linear-gradient(135deg,#7a5c1a,#5a3d0a)",
            "pbg":     "rgba(160,130,80,.12)",
            "pattern": "radial-gradient(ellipse at 30% 70%,rgba(120,80,20,.2) 0%,transparent 50%)",
        },
    },
    "cyberpunk": {
        "name": "⚡ Cyberpunk", "emoji": "⚡",
        "desc": "Neon rain, synth beats, and infinite knowledge downloads.",
        "unlock_level": 5,
        "font_display": "Orbitron", "font_body": "Share Tech Mono",
        "c": {
            "bg":      "#020812", "bg2": "#060e1e",
            "card":    "rgba(0,255,200,.05)", "border": "rgba(0,255,200,.2)",
            "accent":  "#00ffe0", "accent2": "#ff00aa",
            "txt":     "#e0fff8", "txt2": "#60c0b0",
            "xpbar":   "linear-gradient(90deg,#00ffe0,#00a8ff,#ff00aa)",
            "glow":    "rgba(0,255,200,.3)",
            "btn":     "linear-gradient(135deg,#004040,#002030)",
            "pbg":     "rgba(0,255,200,.08)",
            "pattern": "radial-gradient(ellipse at 0% 100%,rgba(0,255,200,.1) 0%,transparent 50%),radial-gradient(ellipse at 100% 0%,rgba(255,0,170,.1) 0%,transparent 50%)",
        },
    },
    "retro_arcade": {
        "name": "🕹️ Retro Arcade", "emoji": "🕹️",
        "desc": "Insert coin. Hit start. Knowledge is the high score.",
        "unlock_level": 8,
        "font_display": "Press Start 2P", "font_body": "VT323",
        "c": {
            "bg":      "#0a0015", "bg2": "#130025",
            "card":    "rgba(255,50,255,.07)", "border": "rgba(255,50,255,.25)",
            "accent":  "#ff50ff", "accent2": "#ffff00",
            "txt":     "#ffffff", "txt2": "#cc88ff",
            "xpbar":   "linear-gradient(90deg,#ff50ff,#ffff00,#00ffff)",
            "glow":    "rgba(255,50,255,.3)",
            "btn":     "linear-gradient(135deg,#440088,#220044)",
            "pbg":     "rgba(255,50,255,.1)",
            "pattern": "radial-gradient(ellipse at 50% 50%,rgba(100,0,200,.2) 0%,transparent 70%)",
        },
    },
    "aquarium": {
        "name": "🐠 Aquarium", "emoji": "🐠",
        "desc": "Study while the fish judge you. They're proud, actually.",
        "unlock_level": 12,
        "font_display": "Comfortaa", "font_body": "Nunito",
        "c": {
            "bg":      "#010e1a", "bg2": "#031828",
            "card":    "rgba(0,150,255,.07)", "border": "rgba(0,200,255,.2)",
            "accent":  "#00c8ff", "accent2": "#00ff99",
            "txt":     "#d0f4ff", "txt2": "#60a8c0",
            "xpbar":   "linear-gradient(90deg,#00c8ff,#00ff99)",
            "glow":    "rgba(0,200,255,.3)",
            "btn":     "linear-gradient(135deg,#003050,#001830)",
            "pbg":     "rgba(0,150,255,.1)",
            "pattern": "radial-gradient(ellipse at 50% 100%,rgba(0,50,150,.4) 0%,transparent 60%)",
        },
    },
    "space_station": {
        "name": "🚀 Space Station", "emoji": "🚀",
        "desc": "In space, no one can hear you procrastinate.",
        "unlock_level": 18,
        "font_display": "Exo 2", "font_body": "Rajdhani",
        "c": {
            "bg":      "#020208", "bg2": "#060615",
            "card":    "rgba(100,80,255,.07)", "border": "rgba(120,100,255,.2)",
            "accent":  "#8870ff", "accent2": "#ff6688",
            "txt":     "#e8e8ff", "txt2": "#8888cc",
            "xpbar":   "linear-gradient(90deg,#8870ff,#ff6688,#ffaa00)",
            "glow":    "rgba(120,100,255,.3)",
            "btn":     "linear-gradient(135deg,#2a1a5a,#180a40)",
            "pbg":     "rgba(100,80,255,.1)",
            "pattern": "radial-gradient(ellipse at 70% 30%,rgba(80,60,200,.2) 0%,transparent 50%),radial-gradient(ellipse at 20% 80%,rgba(200,60,100,.15) 0%,transparent 50%)",
        },
    },
}

FONT_IMPORTS = {
    "Playfair Display": "Playfair+Display:wght@400;600;700",
    "Lora":             "Lora:wght@400;500",
    "Cinzel":           "Cinzel:wght@400;600;700",
    "EB Garamond":      "EB+Garamond:wght@400;500",
    "Orbitron":         "Orbitron:wght@400;600;700;900",
    "Share Tech Mono":  "Share+Tech+Mono",
    "Press Start 2P":   "Press+Start+2P",
    "VT323":            "VT323",
    "Comfortaa":        "Comfortaa:wght@400;600;700",
    "Nunito":           "Nunito:wght@400;500;600",
    "Exo 2":            "Exo+2:wght@400;600;700",
    "Rajdhani":         "Rajdhani:wght@400;500;600",
}

def build_css(theme_key):
    t = THEMES.get(theme_key, THEMES["cozy_cafe"])
    c = t["c"]
    fd, fb = t["font_display"], t["font_body"]
    imports = "\n".join(
        f"@import url('https://fonts.googleapis.com/css2?family={FONT_IMPORTS[f]}&display=swap');"
        for f in {fd, fb} if f in FONT_IMPORTS
    )
    return f"""
{imports}
:root{{
  --bg:{c['bg']};--bg2:{c['bg2']};--card:{c['card']};--border:{c['border']};
  --accent:{c['accent']};--accent2:{c['accent2']};--txt:{c['txt']};--txt2:{c['txt2']};
  --xpbar:{c['xpbar']};--glow:{c['glow']};--btn:{c['btn']};--pbg:{c['pbg']};
  --fd:'{fd}',serif;--fb:'{fb}',sans-serif;
}}
.stApp{{background:{c['bg']};background-image:{c['pattern']};background-attachment:fixed;font-family:var(--fb);color:var(--txt);min-height:100vh;}}
#MainMenu,footer,header,.stDeployButton{{display:none!important;}}
h1,h2,h3{{font-family:var(--fd);color:var(--txt);}}
[data-testid="stSidebar"]{{background:{c['bg2']}!important;border-right:1px solid var(--border);}}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label{{color:var(--txt2)!important;}}

/* Cards */
.card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px 24px;
  margin-bottom:16px;backdrop-filter:blur(12px);
  box-shadow:0 4px 24px rgba(0,0,0,.3),0 0 40px var(--glow);
  transition:transform .2s,box-shadow .2s;}}
.card:hover{{transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,.4),0 0 60px var(--glow);}}

/* XP bar */
.xptrack{{background:var(--pbg);border-radius:20px;height:16px;overflow:hidden;border:1px solid var(--border);margin:8px 0;}}
.xpfill{{height:100%;background:var(--xpbar);border-radius:20px;
  box-shadow:0 0 10px var(--glow);transition:width .8s cubic-bezier(.4,0,.2,1);
  animation:shim 2s infinite;}}
@keyframes shim{{0%,100%{{opacity:.9}}50%{{opacity:1}}}}

/* Timer */
.timerbig{{font-family:var(--fd);font-size:clamp(48px,8vw,80px);color:var(--accent);
  text-align:center;text-shadow:0 0 30px var(--glow);letter-spacing:.05em;padding:20px 0;}}

/* Stat box */
.sbox{{background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:16px;text-align:center;backdrop-filter:blur(8px);}}
.snum{{font-family:var(--fd);font-size:2rem;font-weight:700;color:var(--accent);
  text-shadow:0 0 20px var(--glow);display:block;}}
.slbl{{font-size:.75rem;color:var(--txt2);text-transform:uppercase;letter-spacing:.1em;
  margin-top:4px;display:block;}}

/* Mascot */
.mascot{{text-align:center;padding:20px;animation:flt 3s ease-in-out infinite;}}
@keyframes flt{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
.mbubble{{background:var(--card);border:1px solid var(--border);border-radius:12px 12px 12px 0;
  padding:12px 16px;margin-top:12px;font-style:italic;color:var(--txt2);font-size:.9rem;}}

/* Buttons */
.stButton>button{{background:var(--btn)!important;color:var(--txt)!important;
  border:1px solid var(--border)!important;border-radius:10px!important;
  font-family:var(--fd)!important;padding:10px 24px!important;
  transition:all .2s!important;box-shadow:0 0 20px var(--glow)!important;}}
.stButton>button:hover{{transform:translateY(-1px)!important;
  box-shadow:0 4px 20px var(--glow),0 0 40px var(--glow)!important;
  border-color:var(--accent)!important;}}

/* Page title */
.ptitle{{font-family:var(--fd);font-size:clamp(1.8rem,4vw,2.8rem);color:var(--txt);
  text-shadow:0 0 30px var(--glow);margin-bottom:4px;}}
.psub{{color:var(--txt2);font-size:.9rem;margin-bottom:24px;}}

/* Quest */
.qitem{{background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:12px 16px;margin-bottom:8px;}}

/* Level-up banner */
.lvlup{{background:linear-gradient(135deg,var(--card),rgba(255,255,255,.05));
  border:2px solid var(--accent);border-radius:16px;padding:20px;text-align:center;
  box-shadow:0 0 60px var(--glow);animation:pglow 1s ease-in-out;}}
@keyframes pglow{{0%{{box-shadow:0 0 20px var(--glow)}}50%{{box-shadow:0 0 80px var(--glow)}}100%{{box-shadow:0 0 60px var(--glow)}}}}

/* Badge */
.badge{{background:var(--card);border:1px solid var(--accent);border-radius:8px;
  padding:20px 16px;text-align:center;box-shadow:0 0 15px var(--glow);}}
.badge-locked{{opacity:.35;border-color:var(--border);box-shadow:none;}}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{{background:var(--bg2);border-radius:10px;padding:4px;gap:4px;}}
.stTabs [data-baseweb="tab"]{{background:transparent!important;color:var(--txt2)!important;
  border-radius:8px!important;font-family:var(--fd)!important;}}
.stTabs [aria-selected="true"]{{background:var(--card)!important;color:var(--accent)!important;
  box-shadow:0 0 20px var(--glow)!important;}}

/* Inputs */
.stNumberInput input,.stTextInput input{{
  background:var(--card)!important;color:var(--txt)!important;border-color:var(--border)!important;}}
.stSelectbox>div>div{{background:var(--card)!important;border-color:var(--border)!important;color:var(--txt)!important;}}
[data-testid="metric-container"]{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px!important;}}
[data-testid="metric-container"] label{{color:var(--txt2)!important;}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{color:var(--accent)!important;font-family:var(--fd);}}
::-webkit-scrollbar{{width:6px;}}
::-webkit-scrollbar-track{{background:var(--bg2);}}
::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px;}}
"""

# ============================================================
#  STREAMLIT APP
# ============================================================

st.set_page_config(page_title="✨ Study RPG", page_icon="📚", layout="wide", initial_sidebar_state="expanded")

# ── Session state ──────────────────────────────────────────
def _init():
    defaults = {
        "player":               load_player(),
        "timer_running":        False,
        "timer_start":          None,
        "timer_mode":           "study",
        "timer_duration":       25 * 60,
        "time_remaining":       25 * 60,
        "study_mins_set":       25,
        "break_mins_set":       5,
        "show_level_up":        False,
        "new_level":            1,
        "new_achievements":     [],
        "page":                 "🏠 Home",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Apply CSS ──────────────────────────────────────────────
p = st.session_state.player
st.markdown(f"<style>{build_css(p.get('theme','cozy_cafe'))}</style>", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────
def H(html): st.markdown(html, unsafe_allow_html=True)

def card(content):
    H(f'<div class="card">{content}</div>')

def xp_bar(pct, extra_style=""):
    H(f'<div class="xptrack" style="{extra_style}"><div class="xpfill" style="width:{pct}%;"></div></div>')

def stat_box(value, label):
    return f'<div class="sbox"><span class="snum">{value}</span><span class="slbl">{label}</span></div>'

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    p = st.session_state.player
    theme = THEMES.get(p.get("theme","cozy_cafe"), THEMES["cozy_cafe"])
    H(f"""
    <div style="text-align:center;padding:12px 0;">
      <div style="font-family:var(--fd);font-size:1.4rem;color:var(--accent);">{theme['emoji']} Study RPG</div>
      <div style="color:var(--txt2);font-size:.75rem;margin-top:4px;">{theme['name']}</div>
    </div>""")
    st.markdown("---")

    level = p.get("level", 1)
    xp    = p.get("xp", 0)
    xp_in = xp % 100
    H(f"""
    <div style="margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
        <span style="font-family:var(--fd);color:var(--accent);font-weight:600;">⚔️ Level {level}</span>
        <span style="color:var(--txt2);font-size:.8rem;">{xp_in}/100 XP</span>
      </div>
      <div class="xptrack"><div class="xpfill" style="width:{xp_in}%;"></div></div>
      <div style="color:var(--txt2);font-size:.7rem;margin-top:4px;text-align:center;">{get_level_title(level)}</div>
    </div>""")

    streak = p.get("streak", 0)
    mins_t = p.get("total_study_minutes", 0)
    H(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;">
      {stat_box(('🔥' if streak>0 else '💤')+str(streak), 'Day Streak')}
      {stat_box(f"{mins_t//60}h{mins_t%60}m", 'Studied')}
    </div>""")

    st.markdown("---")
    for pg in ["🏠 Home","⏱️ Timer","🗺️ Quests","🎭 Themes","📊 Stats","🏆 Achievements"]:
        if st.button(pg, key=f"nav_{pg}", use_container_width=True):
            st.session_state.page = pg
            st.rerun()

    st.markdown("---")
    H(f"""
    <div style="text-align:center;padding:8px;">
      <div style="font-size:.7rem;color:var(--txt2);text-transform:uppercase;letter-spacing:.1em;">Active Title</div>
      <div style="color:var(--accent);font-family:var(--fd);font-size:.9rem;margin-top:4px;">"{p.get('active_title','Student')}"</div>
    </div>""")

# ── Complete session handler ────────────────────────────────
def complete_session():
    p = st.session_state.player
    if st.session_state.timer_mode == "study":
        mins    = st.session_state.study_mins_set
        xp_earn = calculate_xp_gain(mins)
        p = add_session(p, mins, xp_earn)
        p, leveled_up, new_lv = add_xp(p, xp_earn)
        p, _ = update_streak(p)
        p, new_ach = check_achievements(p)

        # Quest progress
        for i, q in enumerate(p.get("daily_quests", [])):
            if not q.get("done"):
                completed = False
                if q["type"] == "sessions"      and p["sessions_completed"] >= q["target"]: completed = True
                elif q["type"] == "minutes"     and p["total_study_minutes"] >= q["target"]: completed = True
                elif q["type"] == "long_session" and mins >= q["target"]: completed = True
                if completed:
                    p["daily_quests"][i]["done"] = True
                    p, _, _ = add_xp(p, q["xp"])

        save_player(p)
        st.session_state.player           = p
        st.session_state.new_achievements = new_ach
        if leveled_up:
            st.session_state.show_level_up = True
            st.session_state.new_level     = new_lv

        # Switch to break
        st.session_state.timer_mode      = "break"
        st.session_state.timer_duration  = st.session_state.break_mins_set * 60
        st.session_state.time_remaining  = st.session_state.break_mins_set * 60
    else:
        st.session_state.timer_mode      = "study"
        st.session_state.timer_duration  = st.session_state.study_mins_set * 60
        st.session_state.time_remaining  = st.session_state.study_mins_set * 60

    st.session_state.timer_running = False
    st.session_state.timer_start   = None
    st.rerun()

# ── Pages ──────────────────────────────────────────────────
page = st.session_state.page

# ════════════════════ HOME ════════════════════
if page == "🏠 Home":
    p = st.session_state.player
    p = get_or_refresh_quests(p)
    st.session_state.player = p

    hour     = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    H(f'<div class="ptitle">{greeting}, {p.get("name","Scholar")}! ✨</div>')
    H('<div class="psub">The knowledge won\'t gain itself. (Well, unless you start a session.)</div>')

    # Level-up banner
    if st.session_state.show_level_up:
        H(f"""<div class="lvlup">
          <div style="font-family:var(--fd);font-size:2rem;color:var(--accent);">⬆️ LEVEL UP! ⬆️</div>
          <div style="font-size:1.2rem;color:var(--txt);margin:8px 0;">You're now Level {st.session_state.new_level}!</div>
          <div style="color:var(--txt2);">{get_level_title(st.session_state.new_level)} · New rewards may have unlocked!</div>
        </div>""")
        if st.button("🎉 Awesome!"):
            st.session_state.show_level_up = False
            st.rerun()
        st.stop()

    for ach_key in st.session_state.new_achievements:
        ach = ACHIEVEMENTS.get(ach_key, {})
        st.success(f"{ach.get('icon','🏆')} Achievement Unlocked: **{ach.get('name','')}** — {ach.get('desc','')}")
    st.session_state.new_achievements = []

    col1, col2 = st.columns([3, 2])

    with col1:
        level = p.get("level",1); xp = p.get("xp",0)
        xp_in = xp % 100; sessions = p.get("sessions_completed",0)

        H(f"""<div class="card">
          <div style="font-family:var(--fd);font-size:1.1rem;color:var(--accent);margin-bottom:12px;">⚡ Your Stats</div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;">
            {stat_box(level,'Level')}
            {stat_box(('🔥' if p.get('streak',0)>=3 else '')+str(p.get('streak',0)),'Streak')}
            {stat_box(sessions,'Sessions')}
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:var(--txt2);font-size:.85rem;">XP Progress</span>
            <span style="color:var(--accent);font-size:.85rem;">{xp_in}/100</span>
          </div>
          <div class="xptrack"><div class="xpfill" style="width:{xp_in}%;"></div></div>
          <div style="color:var(--txt2);font-size:.75rem;margin-top:4px;">Total XP: {xp} · {get_level_title(level)}</div>
        </div>""")

        # Quests Block (Fixed layout and broken structural div strings here)
        quests_html = f"""<div class="card">
          <div style="font-family:var(--fd);font-size:1.1rem;color:var(--accent);margin-bottom:12px;">📜 Today's Quests</div>"""
        
        for i, q in enumerate(p.get("daily_quests",[])):
            done = q.get("done", False)
            icon = "✅" if done else "◻️"
            alpha = ".5" if done else "1"
            quests_html += f"""
            <div class="qitem" style="opacity:{alpha};display:flex;align-items:center;gap:12px;margin-bottom:8px;">
              <span style="font-size:1.2rem;">{icon}</span>
              <div style="flex:1;">
                <div style="color:var(--txt);font-size:.9rem;">{q["text"]}</div>
                <div style="color:var(--accent);font-size:.75rem;">+{q["xp"]} XP</div>
              </div>
            </div>"""
        
        quests_html += "</div>"
        H(quests_html)

        # Action Buttons for Quest Completions rendered cleanly below
        for i, q in enumerate(p.get("daily_quests",[])):
            if not q.get("done") and q.get("type") == "wellness":
                if st.button(f"✔ Mark Done: {q['text']}", key=f"wq_{i}", use_container_width=True):
                    p["daily_quests"][i]["done"] = True
                    p, lv, nl = add_xp(p, q["xp"])
                    save_player(p); st.session_state.player = p
                    if lv: st.session_state.show_level_up=True; st.session_state.new_level=nl
                    st.rerun()

        st.write("") # subtle padding spacer
        if st.button("⚡ Start Studying Now!", use_container_width=True):
            st.session_state.page = "⏱️ Timer"; st.rerun()

    with col2:
        mood   = get_mascot_mood(p)
        emoji  = MASCOT_EMOJI[mood]
        label  = MASCOT_MOOD_LABEL[mood]
        line   = mascot_line(mood)

        H(f"""<div class="card">
          <div class="mascot"><span style="font-size:80px;filter:drop-shadow(0 0 20px var(--glow));">{emoji}</span>
            <div style="color:var(--txt2);font-size:.75rem;margin-top:8px;text-transform:uppercase;letter-spacing:.08em;">{label}</div>
          </div>
          <div class="mbubble">"{line}"</div>
        </div>""")

        streak = p.get("streak",0)
        smsg = (
            "Start your first session to ignite the streak! 🌟" if streak==0 else
            "Day 1! The journey of a thousand pages begins..." if streak==1 else
            "Building momentum! Don't stop now!" if streak<3 else
            "You're on FIRE! The streak is real!" if streak<7 else
            f"{streak} days?! You are BUILT different."
        )
        H(f"""<div class="card" style="text-align:center;">
          <div style="font-size:2.5rem;">{'🔥'*min(streak,5) if streak>0 else '💫'}</div>
          <div style="font-family:var(--fd);font-size:1.5rem;color:var(--accent);margin:8px 0;">{streak} Day Streak</div>
          <div style="color:var(--txt2);font-size:.85rem;font-style:italic;">{smsg}</div>
        </div>""")

        tm = p.get("total_study_minutes",0)
        H(f"""<div class="card" style="text-align:center;">
          <div style="font-size:1.8rem;color:var(--accent);font-family:var(--fd);">{tm//60}h {tm%60}m</div>
          <div style="color:var(--txt2);font-size:.8rem;margin-top:4px;">Total Study Time ⏳</div>
          <div style="color:var(--txt2);font-size:.75rem;margin-top:8px;font-style:italic;">
            {"That's practically a part-time job. Incredible." if tm//60>=10 else "Every minute counts! Keep going." if tm>=60 else "Your first hour awaits. You've got this!"}
          </div>
        </div>""")

# ════════════════════ TIMER ════════════════════
elif page == "⏱️ Timer":
    H('<div class="ptitle">⏱️ Pomodoro Timer</div>')
    H('<div class="psub">Focus. The XP won\'t farm itself.</div>')

    col_main, col_side = st.columns([3, 2])

    with col_main:
        H('<div class="card">')

        if not st.session_state.timer_running and st.session_state.timer_mode == "study":
            c1, c2 = st.columns(2)
            with c1:
                sm = st.number_input("Study Duration (min)", 5, 180, st.session_state.study_mins_set, 5)
                st.session_state.study_mins_set = sm
            with c2:
                bm = st.number_input("Break Duration (min)", 1, 60, st.session_state.break_mins_set, 1)
                st.session_state.break_mins_set = bm

        # Recalc remaining if running
        tr = st.session_state.time_remaining
        if st.session_state.timer_running and st.session_state.timer_start:
            elapsed = time.time() - st.session_state.timer_start
            tr = max(0, st.session_state.timer_duration - int(elapsed))
            st.session_state.time_remaining = tr

        mode_lbl = "📚 Study Time" if st.session_state.timer_mode == "study" else "☕ Break Time"
        pct      = int((1 - tr / st.session_state.timer_duration) * 100) if st.session_state.timer_duration else 100
        xp_prev  = calculate_xp_gain(st.session_state.study_mins_set)

        H(f"""
        <div style="text-align:center;margin:8px 0;">
          <div style="color:var(--txt2);font-size:.85rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">{mode_lbl}</div>
          <div class="timerbig">{tr//60:02d}:{tr%60:02d}</div>
          <div class="xptrack" style="max-width:400px;margin:8px auto;">
            <div class="xpfill" style="width:{pct}%;"></div>
          </div>
          <div style="color:var(--txt2);font-size:.8rem;margin-top:6px;">
            {pct}% complete · XP on finish: ~{xp_prev} ✨
          </div>
        </div>""")

        b1, b2, b3 = st.columns(3)
        with b1:
            if not st.session_state.timer_running:
                if st.button("▶ Start", use_container_width=True):
                    dur = (st.session_state.study_mins_set if st.session_state.timer_mode=="study"
                           else st.session_state.break_mins_set) * 60
                    st.session_state.timer_duration  = dur
                    st.session_state.time_remaining  = dur
                    st.session_state.timer_start     = time.time()
                    st.session_state.timer_running   = True
                    st.rerun()
            else:
                if st.button("⏸ Pause", use_container_width=True):
                    if st.session_state.timer_start:
                        elapsed = time.time() - st.session_state.timer_start
                        remaining = max(0, st.session_state.timer_duration - int(elapsed))
                        st.session_state.time_remaining = remaining
                        st.session_state.timer_duration = remaining
                    st.session_state.timer_running = False
                    st.session_state.timer_start   = None
                    st.rerun()
        with b2:
            if st.button("↺ Reset", use_container_width=True):
                st.session_state.timer_running   = False
                st.session_state.timer_start     = None
                st.session_state.timer_mode      = "study"
                dur = st.session_state.study_mins_set * 60
                st.session_state.timer_duration  = dur
                st.session_state.time_remaining  = dur
                st.rerun()
        with b3:
            if st.button("✅ Complete", use_container_width=True):
                complete_session()

        if st.session_state.timer_running and tr <= 0:
            complete_session()

        H('</div>')

        if st.session_state.timer_running:
            time.sleep(1)
            st.rerun()

    with col_side:
        sm       = st.session_state.study_mins_set
        xp_earn  = calculate_xp_gain(sm)
        bonus    = xp_earn - sm * 2
        bonus_ln = (f"<div style='color:var(--txt2);font-size:.9rem;margin-bottom:8px;'>Bonus XP: <span style='color:var(--accent);'>+{bonus} 🎁</span></div>"
                    if bonus > 0 else "")
        note     = ("Bonus unlocked for sessions 45min+!" if sm >= 45
                    else f"{45-sm} more minutes for a bonus!")

        H(f"""<div class="card">
          <div style="font-family:var(--fd);color:var(--accent);margin-bottom:12px;">⚡ XP Rewards</div>
          <div style="color:var(--txt2);font-size:.9rem;margin-bottom:8px;">Base XP: <span style="color:var(--txt);">{sm*2}</span></div>
          {bonus_ln}
          <div style="color:var(--accent);font-size:1.2rem;font-family:var(--fd);">Total: +{xp_earn} XP</div>
          <div style="color:var(--txt2);font-size:.75rem;margin-top:8px;font-style:italic;">{note}</div>
        </div>""")

        mood  = get_mascot_mood(st.session_state.player)
        emoji = MASCOT_EMOJI[mood]
        line  = mascot_line(mood)
        H(f"""<div class="card">
          <div style="text-align:center;font-size:3rem;margin-bottom:12px;">{emoji}</div>
          <div class="mbubble">"{line}"</div>
        </div>""")

        tip = random.choice([
            "📵 Put your phone face-down for max focus.",
            "💧 Hydrate! Your brain is 75% water.",
            "🎵 Lo-fi beats are scientifically cozy.",
            "✏️ Write it down — don't just read.",
            "🪟 Natural light = natural energy.",
            "🧠 Teach it to a rubber duck. Works every time.",
        ])
        H(f"""<div class="card">
          <div style="color:var(--txt2);font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">💡 Study Tip</div>
          <div style="color:var(--txt);font-size:.9rem;">{tip}</div>
        </div>""")

# ════════════════════ QUESTS ════════════════════
elif page == "🗺️ Quests":
    p = st.session_state.player
    p = get_or_refresh_quests(p)
    st.session_state.player = p

    H('<div class="ptitle">🗺️ Daily Quests</div>')
    H('<div class="psub">Complete your quests. Earn glory. Also XP.</div>')

    col1, col2 = st.columns([3, 2])
    quests = p.get("daily_quests", [])

    with col1:
        for i, q in enumerate(quests):
            done  = q.get("done", False)
            icon  = "✅" if done else "⚔️"
            alpha = ".5" if done else "1"
            H(f"""<div class="card" style="opacity:{alpha};">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <span style="font-size:1.5rem;margin-right:12px;">{icon}</span>
                  <span style="font-family:var(--fd);color:var(--txt);font-size:1rem;">{q['text']}</span>
                </div>
                <div style="color:var(--accent);font-size:.9rem;white-space:nowrap;margin-left:12px;">+{q['xp']} XP</div>
              </div>
              {"<div style='color:var(--accent);font-size:.8rem;margin-top:8px;'>✨ Quest Complete!</div>" if done else ""}
            </div>""")
            if not done and q.get("type") == "wellness":
                if st.button(f"✔ Mark Done", key=f"qq_{i}", use_container_width=True):
                    p["daily_quests"][i]["done"] = True
                    p, lv, nl = add_xp(p, q["xp"])
                    save_player(p); st.session_state.player = p
                    if lv: st.session_state.show_level_up=True; st.session_state.new_level=nl
                    st.rerun()

    with col2:
        done_n = sum(1 for q in quests if q.get("done"))
        total_n = len(quests)
        H(f"""<div class="card">
          <div style="font-family:var(--fd);color:var(--accent);margin-bottom:16px;font-size:1.1rem;">📊 Quest Progress</div>
          <div class="xptrack"><div class="xpfill" style="width:{int(done_n/total_n*100) if total_n else 0}%;"></div></div>
          <div style="text-align:center;margin-top:12px;font-size:1.5rem;color:var(--txt);">{done_n}/{total_n} Complete</div>
          <div style="color:var(--txt2);font-size:.8rem;text-align:center;margin-top:8px;">
            {"🏆 All quests done! Legend." if done_n==total_n else f"{total_n-done_n} quest(s) remaining"}
          </div>
        </div>""")
        H("""<div class="card">
          <div style="font-family:var(--fd);color:var(--accent);margin-bottom:8px;">🔄 Quest Reset</div>
          <div style="color:var(--txt2);font-size:.85rem;">Quests refresh daily at midnight. Complete them before they vanish into the void!</div>
        </div>""")

# ════════════════════ THEMES ════════════════════
elif page == "🎭 Themes":
    p = st.session_state.player
    H('<div class="ptitle">🎭 Visual Themes</div>')
    H('<div class="psub">Dress your study dungeon. Themes unlock as you level up!</div>')

    unlocked = p.get("unlocked_themes", ["cozy_cafe"])
    current  = p.get("theme", "cozy_cafe")
    level    = p.get("level", 1)

    for tk, th in THEMES.items():
        is_curr     = tk == current
        is_unlocked = tk in unlocked
        can_unlock  = level >= th.get("unlock_level", 1)

        if is_curr:
            border = "border:2px solid var(--accent);"
            tag    = "✨ ACTIVE"; tc = "var(--accent)"
        elif is_unlocked:
            border = ""; tag = "✅ Unlocked"; tc = "#44cc88"
        elif can_unlock:
            border = "opacity:.7;"; tag = f"🔓 Available (Lv.{th['unlock_level']})"; tc = "var(--txt2)"
        else:
            border = "opacity:.4;"; tag = f"🔒 Locked (Lv.{th['unlock_level']})"; tc = "var(--txt2)"

        H(f"""<div class="card" style="{border}">
          <div style="display:flex;justify-content:space-between;align-items:start;">
            <div>
              <div style="font-family:var(--fd);font-size:1.2rem;color:var(--txt);">{th['name']}</div>
              <div style="color:var(--txt2);font-size:.85rem;margin-top:4px;font-style:italic;">{th['desc']}</div>
            </div>
            <div style="color:{tc};font-size:.8rem;white-space:nowrap;margin-left:12px;padding-top:4px;">{tag}</div>
          </div>
        </div>""")

        if is_unlocked and not is_curr:
            if st.button(f"Switch to {th['name']}", key=f"sw_{tk}"):
                p["theme"] = tk; save_player(p); st.session_state.player = p; st.rerun()
        elif can_unlock and not is_unlocked:
            if st.button(f"Unlock {th['name']}", key=f"ul_{tk}"):
                p["unlocked_themes"].append(tk); p["theme"] = tk
                save_player(p); st.session_state.player = p; st.rerun()

# ════════════════════ STATS ════════════════════
elif page == "📊 Stats":
    p = st.session_state.player
    history  = load_history()
    sessions = history.get("sessions", [])

    H('<div class="ptitle">📊 Study Statistics</div>')
    H('<div class="psub">The numbers never lie. (They\'re very impressed.)</div>')

    tm   = p.get("total_study_minutes",0)
    sc   = p.get("sessions_completed",0)
    avg  = tm // sc if sc > 0 else 0
    cols = st.columns(4)
    for col, val, lbl, icon in zip(cols,
        [f"{tm//60}h {tm%60}m", str(sc), f"{avg}m", str(p.get("streak",0))],
        ["Total Study Time","Sessions Done","Avg Session","Current Streak"],
        ["⏰","📚","⚡","🔥"]):
        with col:
            H(f"""<div class="card" style="text-align:center;">
              <div style="font-size:1.5rem;margin-bottom:8px;">{icon}</div>
              <div style="font-family:var(--fd);font-size:1.5rem;color:var(--accent);">{val}</div>
              <div style="color:var(--txt2);font-size:.75rem;margin-top:4px;">{lbl}</div>
            </div>""")

    if sessions:
        H("""<div class="card" style="margin-top:16px;">
          <div style="font-family:var(--fd);color:var(--accent);margin-bottom:12px;font-size:1.1rem;">📋 Recent Sessions</div>""")
        for s in reversed(sessions[-10:]):
            ds = s["date"][:16].replace("T"," ")
            H(f"""<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);">
              <span style="color:var(--txt2);font-size:.85rem;">{ds}</span>
              <span style="color:var(--txt);">{s['minutes']} min</span>
              <span style="color:var(--accent);">+{s['xp_gained']} XP</span>
            </div>""")
        H("</div>")
    else:
        H("""<div class="card" style="text-align:center;padding:40px;">
          <div style="font-size:3rem;margin-bottom:12px;">🌱</div>
          <div style="color:var(--txt2);">No sessions yet. Your legend begins with the first timer. ✨</div>
        </div>""")

# ════════════════════ ACHIEVEMENTS ════════════════════
elif page == "🏆 Achievements":
    p = st.session_state.player
    earned = p.get("achievements", [])
    H('<div class="ptitle">🏆 Achievements</div>')
    H('<div class="psub">The badges of your academic journey. Wear them with pride.</div>')

    cols = st.columns(3)
    for i, (key, ach) in enumerate(ACHIEVEMENTS.items()):
        unlocked = key in earned
        with cols[i % 3]:
            cls = "badge" if unlocked else "badge badge-locked"
            glow = "box-shadow:0 0 20px var(--glow);" if unlocked else ""
            H(f"""<div class="card {cls}" style="{glow}">
              <div style="font-size:2rem;margin-bottom:8px;">{ach['icon']}</div>
              <div style="font-family:var(--fd);color:var(--accent);font-size:.95rem;margin-bottom:6px;">{ach['name']}</div>
              <div style="color:var(--txt2);font-size:.75rem;">{ach['desc']}</div>
              {"<div style='color:var(--accent);font-size:.7rem;margin-top:8px;'>✨ UNLOCKED</div>" if unlocked else "<div style='color:var(--txt2);font-size:.7rem;margin-top:8px;'>🔒 Locked</div>"}
            </div>""")
