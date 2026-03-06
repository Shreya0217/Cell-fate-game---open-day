import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap

st.set_page_config(layout="wide", page_title="Inside the tumor - game simulation of cancer growth")

# ── Compact CSS for single-screen fit on 24" ──────────────────────────────────
st.markdown("""
<style>
    /* shrink all default Streamlit padding */
    .block-container { padding: 0.5rem 1.2rem 0.2rem 1.2rem !important; max-width: 100% !important; }
    h1 { font-size: 1.3rem !important; margin: 0 !important; padding: 0 !important; }
    h2, h3 { font-size: 0.95rem !important; margin: 0 0 2px 0 !important; padding: 0 !important; }
    .stButton > button {
        padding: 4px 8px !important;
        font-size: 0.78rem !important;
        height: 34px !important;
        width: 100% !important;
    }
    .stSlider { padding: 0 !important; }
    .stProgress > div > div { height: 8px !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.2rem !important; }
    div[data-testid="column"] { padding: 0 0.25rem !important; }
    .stMarkdown p { margin: 1px 0 !important; font-size: 0.82rem !important; }
    .stCaption { font-size: 0.72rem !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    header { display: none !important; }
    footer { display: none !important; }
    .element-container { margin-bottom: 2px !important; }
    /* hide slider labels to save space */
    .stSlider label { font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GRID_SIZE   = 30
MIN_STEM    = 150
WIN_STEPS   = 200

EMPTY  = 0
DIFF   = 1
SELF   = 2
CANCER = 3
IMMUNE = 4

CELL_COLORS = {
    EMPTY:  "#0d0d0d",
    DIFF:   "#22c55e",
    SELF:   "#3b82f6",
    CANCER: "#a855f7",
    IMMUNE: "#ef4444",
}

def get_cancer_rate(steps):
    return 8 + min(steps // 20, 28)

# ─────────────────────────────────────────────────────────────────────────────
# GRID INIT
# ─────────────────────────────────────────────────────────────────────────────
def init_grid():
    return np.random.choice(
        [SELF, DIFF, EMPTY],
        size=(GRID_SIZE, GRID_SIZE),
        p=[0.15, 0.75, 0.10]
    )

def get_neighbors(grid, i, j):
    neighbors = []
    for x in range(max(0, i-1), min(GRID_SIZE, i+2)):
        for y in range(max(0, j-1), min(GRID_SIZE, j+2)):
            if (x, y) != (i, j):
                neighbors.append(grid[x, y])
    return neighbors

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE RULES
# ─────────────────────────────────────────────────────────────────────────────
def update_cell(cell, neighbors):
    n_self   = neighbors.count(SELF)
    n_can    = neighbors.count(CANCER)
    n_immune = neighbors.count(IMMUNE)

    if cell == EMPTY:
        if n_can >= 3 and np.random.rand() < 0.6 + (n_can - 3) * 0.1:
            return CANCER
        if n_immune >= 1 and np.random.rand() < 0.1:
            return IMMUNE
        if n_self >= 2:
            return SELF if np.random.rand() < 0.6 else DIFF
        if neighbors.count(DIFF) >= 3 and np.random.rand() < 0.4:
            return DIFF
        return EMPTY

    if cell == SELF:
        dp = 0.02 +  n_can * 0.04
        if np.random.rand() < dp:
            return EMPTY
        if n_can >= 3 and n_immune == 0:
            return CANCER if np.random.rand() < 0.3 else SELF
        if n_self >= 4:
            return DIFF if np.random.rand() < 0.8 else SELF
        return SELF

    if cell == DIFF:
        dp = 0.05 +  n_can * 0.03
        return EMPTY if np.random.rand() < dp else DIFF

    if cell == CANCER:
        if n_immune >= 2 and np.random.rand() < 0.35 * n_immune:
            return EMPTY
        if np.random.rand() < 0.003:
            return EMPTY
        return CANCER

    if cell == IMMUNE:
        if n_can >= 5:
            return EMPTY
        return EMPTY if np.random.rand() < 0.08 else IMMUNE

    return cell

def step(grid):
    new_grid = grid.copy()
    idx = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE)]
    np.random.shuffle(idx)
    for i, j in idx:
        new_grid[i, j] = update_cell(grid[i, j], get_neighbors(grid, i, j))
    return new_grid

# ─────────────────────────────────────────────────────────────────────────────
# PLOT GRID — compact for 24"
# ─────────────────────────────────────────────────────────────────────────────
def plot_grid(grid):
    cmap = ListedColormap([CELL_COLORS[k] for k in sorted(CELL_COLORS)])
    fig, ax = plt.subplots(figsize=(2.6,2.6), dpi=70)
    fig.patch.set_facecolor("#050505")
    ax.set_facecolor("#050505")
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=4, interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    plt.tight_layout(pad=0)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# PIE CHART LEGEND
# ─────────────────────────────────────────────────────────────────────────────
def plot_pie(stats, total):
    labels  = ["Differentiated", "Stem", "Cancer", "Immune", "Empty"]
    keys    = [DIFF, SELF, CANCER, IMMUNE, EMPTY]
    colors  = [CELL_COLORS[k] for k in keys]
    sizes   = [stats.get(k, 0) for k in keys]

    if sum(sizes) == 0:
        return

    fig, ax = plt.subplots(figsize=(3.2, 2.4), dpi=90)
    fig.patch.set_facecolor("#ffffff")
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct=lambda p: f"{p:.0f}%" if p > 3 else "",
        startangle=90,
        wedgeprops=dict(linewidth=0.5, edgecolor="#222"),
        textprops=dict(color="black", fontsize=7),
        pctdistance=0.5,
    )
    for at in autotexts:
        at.set_fontsize(6.5)
        at.set_color("black")

    legend_labels = [f"{l}  ({stats.get(k,0)})" for l, k in zip(labels, keys)]
    ax.legend(
        wedges, legend_labels,
        loc="center left", bbox_to_anchor=(1, 0.5),
        fontsize=6.5, frameon=False,
        labelcolor="black",
    )
    ax.set_facecolor("#ffffff")
    plt.tight_layout(pad=0.2)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
if "grid"      not in st.session_state: st.session_state.grid      = init_grid()
if "steps"     not in st.session_state: st.session_state.steps     = 0
if "game_over" not in st.session_state: st.session_state.game_over = False
if "won"       not in st.session_state: st.session_state.won       = False
if "budget"    not in st.session_state: st.session_state.budget    = 100
if "event_log" not in st.session_state: st.session_state.event_log = []

def log(msg):
    st.session_state.event_log.insert(0, f"[{st.session_state.steps}] {msg}")
    st.session_state.event_log = st.session_state.event_log[:5]

def regulate_stem():
    grid = st.session_state.grid
    sc   = np.sum(grid == SELF)
    if sc < MIN_STEM:
        pos = np.argwhere(grid == EMPTY)
        if len(pos):
            chosen = pos[np.random.choice(len(pos), min(MIN_STEM - sc, len(pos)), replace=False)]
            for x, y in chosen:
                grid[x, y] = SELF

def check_end():
    grid    = st.session_state.grid
    total   = GRID_SIZE * GRID_SIZE
    c_cells = np.sum(grid == CANCER)
    if c_cells >= 0.5 * total:
        st.session_state.game_over = True
    if st.session_state.steps >= WIN_STEPS and c_cells < 0.5* total:
        st.session_state.won = True

# ─────────────────────────────────────────────────────────────────────────────
# COOLDOWNS
# ─────────────────────────────────────────────────────────────────────────────
COSTS = {"chemo": 25, "immune": 30}
CDS   = {"chemo": 10, "immune": 15}

def cd_left(key):
    return max(0, CDS[key] - (st.session_state.steps - st.session_state.get(f"cd_{key}", -999)))

def set_cd(key):
    st.session_state[f"cd_{key}"] = st.session_state.steps

# ─────────────────────────────────────────────────────────────────────────────
# INTERVENTIONS
# ─────────────────────────────────────────────────────────────────────────────
def do_chemo():
    if st.session_state.budget < COSTS["chemo"]: log("❌ Need 25 budget"); return
    g = st.session_state.grid
    killed = sum(1 for pos in np.argwhere(g == CANCER) if np.random.rand() < 0.45 and not g.__setitem__((pos[0], pos[1]), EMPTY))
    for pos in np.argwhere(g == DIFF):
        if np.random.rand() < 0.08: g[pos[0], pos[1]] = EMPTY
    st.session_state.budget -= COSTS["chemo"]; set_cd("chemo")
    log(f"💊 Chemo — {np.sum(st.session_state.grid != CANCER)} healthy cells remain")

def do_immune():
    if st.session_state.budget < COSTS["immune"]: log("❌ Need 30 budget"); return
    g   = st.session_state.grid
    pos = np.argwhere(g == CANCER)
    placed = 0
    if len(pos):
        for cx, cy in pos[np.random.choice(len(pos), min(35, len(pos)), replace=False)]:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and g[nx, ny] == EMPTY and np.random.rand() < 0.3:
                        g[nx, ny] = IMMUNE; placed += 1
    st.session_state.budget -= COSTS["immune"]; set_cd("immune")
    log(f"🛡️ Immune boost — {placed} cells deployed")

# ─────────────────────────────────────────────────────────────────────────────
# RUN SIMULATION
# ─────────────────────────────────────────────────────────────────────────────
def run_steps(n):
    if st.session_state.game_over or st.session_state.won: return
    # nutrients = st.session_state.get("nutrients", 0.3)
    for si in range(n):
        st.session_state.grid   = step(st.session_state.grid)
        st.session_state.steps += 1
        st.session_state.budget = min(100, st.session_state.budget)
        if si % 5 == 0 and si != 0:
            rate = get_cancer_rate(st.session_state.steps)
            diff_pos = np.argwhere(st.session_state.grid == DIFF)
            for _ in range(rate):
                if len(diff_pos) and np.random.rand() < 0.6:
                    pos = diff_pos[np.random.choice(len(diff_pos))]
                    st.session_state.grid[pos[0], pos[1]] = CANCER
                else:
                    x, y = np.random.randint(0, GRID_SIZE, 2)
                    st.session_state.grid[x, y] = CANCER
        check_end()
        if st.session_state.game_over or st.session_state.won: break
    regulate_stem()

# ─────────────────────────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────────────────────────
grid    = st.session_state.grid
total   = GRID_SIZE * GRID_SIZE
uniq, cnts = np.unique(grid, return_counts=True)
stats   = dict(zip(uniq, cnts))
cancer_pct = stats.get(CANCER, 0) / total * 100
steps   = st.session_state.steps
budget  = st.session_state.budget

# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT  —  Title row  +  [controls col | grid col]
# ─────────────────────────────────────────────────────────────────────────────
# ── Title bar ─────────────────────────────────────────────────────────────────
tc1, tc2, tc3 = st.columns([2, 3, 2])
with tc1:
    st.markdown("## 🧬 Inside the tumor - Cancer growth simulation game")
with tc2:
    threat_icon = "🟢" if cancer_pct < 15 else ("🟡" if cancer_pct < 35 else "🔴")
    st.markdown(f"**Cancer** {threat_icon} `{cancer_pct:.1f}%` &nbsp;|&nbsp; "
                f"**Step** `{steps}/{WIN_STEPS}` &nbsp;|&nbsp; ")
with tc3:
    st.progress(min(1.0, steps / WIN_STEPS), text=None)

st.markdown("<hr style='margin:2px 0 4px 0; border-color:#333'>", unsafe_allow_html=True)

# ── Main columns ──────────────────────────────────────────────────────────────
ctrl_col, grid_col = st.columns([1,1], gap="small")

# ─── CONTROLS ─────────────────────────────────────────────────────────────────
with ctrl_col:

    # Budget
    st.markdown("**💰 Treatment Budget**")
    col_b1, col_b2 = st.columns([3,1])
    with col_b1:
        st.progress(budget / 100)
    with col_b2:
        st.markdown(f"`{budget}/100`")

    # st.markdown("<div style='margin:4px 0'></div>", unsafe_allow_html=True)

    # # Nutrient slider (inline, no sidebar)
    # st.markdown("**🌍 Nutrient Level**")
    # nutrients = st.slider(
    #     "nutrients_main", 0.0, 0.6, 0.3,
    #     label_visibility="collapsed",
    #     key="nutrients",
    #     help="Higher nutrients = faster cancer growth"
    # )
    # n_label = "🔴 High (feeds cancer)" if nutrients > 0.4 else ("🟡 Medium" if nutrients > 0.2 else "🟢 Low (slows cancer)")
    # st.caption(n_label)

    # st.markdown("<div style='margin:3px 0'></div>", unsafe_allow_html=True)

    # Interventions
    st.markdown("**🔬 Interventions**")

    i1, i2 = st.columns(2)
    with i1:
        cd_c = cd_left("chemo")
        lbl_c = f"💊 Chemo (💰25)" + (f" ⏳{cd_c}" if cd_c else "")
        dis_c = cd_c > 0 or budget < 25 or st.session_state.game_over or st.session_state.won
        if st.button(lbl_c, disabled=dis_c, use_container_width=True, key="btn_chemo"):
            do_chemo()

    with i2:
        cd_i = cd_left("immune")
        lbl_i = f"🛡️ Immune (💰30)" + (f" ⏳{cd_i}" if cd_i else "")
        dis_i = cd_i > 0 or budget < 30 or st.session_state.game_over or st.session_state.won
        if st.button(lbl_i, disabled=dis_i, use_container_width=True, key="btn_immune"):
            do_immune()

    st.markdown("<div style='margin:3px 0'></div>", unsafe_allow_html=True)

    # Simulation step buttons
    st.markdown("**⏩ Advance Simulation**")
    s1, s2, s3 = st.columns(3)
    with s1:
        if st.button("▶ 10", use_container_width=True, disabled=st.session_state.game_over or st.session_state.won):
            run_steps(10)
    with s2:
        if st.button("▶ 20", use_container_width=True, disabled=st.session_state.game_over or st.session_state.won):
            run_steps(20)
    with s3:
        if st.button("▶ 50", use_container_width=True, disabled=st.session_state.game_over or st.session_state.won):
            run_steps(50)

    if st.button("🔄 Reset", use_container_width=True):
        for k in ["grid","steps","game_over","won","budget","event_log","cd_chemo","cd_immune"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    st.markdown("<div style='margin:3px 0'></div>", unsafe_allow_html=True)

    # Event log (compact)
    if st.session_state.event_log:
        st.markdown("**📋 Log**")
        for e in st.session_state.event_log:
            st.caption(e)

    st.markdown("<div style='margin:4px 0'></div>", unsafe_allow_html=True)

    # Pie chart (dynamic cell legend)
    st.markdown("**🔵 Cell Distribution**")
    plot_pie(stats, total)

# ─── GRID ─────────────────────────────────────────────────────────────────────
with grid_col:
    plot_grid(grid)

# ── GAME END POPUP ─────────────────────────────────────────────
    if st.session_state.won or st.session_state.game_over:

        title = "🏆 Cancer Contained!" if st.session_state.won else "🟣 Cancer Took Over!"
        color = "#22c55e" if st.session_state.won else "#ff4b4b"
        bg = "#d9dedb" if st.session_state.won else "#efddef"

        message = (
            f"Survived {steps} steps with cancer under control."
            if st.session_state.won
            else f"Survived {steps}/{WIN_STEPS} steps — Try Immune Boost earlier."
        )

        st.markdown(f"""
        <style>
        .popup {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: {bg};
            padding: 35px 50px;
            border-radius: 14px;
            border: 3px solid {color};
            text-align: center;
            z-index: 9999;
            box-shadow: 0 0 40px rgba(0,0,0,0.8);
        }}
        </style>

        <div class="popup">
            <h2 style="color:{color}; margin-bottom:10px;">{title}</h2>
            <p style="font-size:16px;">{message}</p>
        </div>
        """, unsafe_allow_html=True)