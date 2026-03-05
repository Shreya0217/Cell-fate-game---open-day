import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# -------------------------
# CONFIG
# -------------------------
GRID_SIZE = 50

# States
EMPTY = 0
DIFF = 1
SELF = 2
CANCER = 3

state_names = {
    EMPTY: "Dead",
    DIFF: "Stable differentiated",
    SELF: "Self-renew",
    CANCER: "Cancer"
}

# -------------------------
# INIT GRID
# -------------------------
def init_grid():
    grid = np.random.choice(
    [SELF, DIFF, EMPTY],
    size=(GRID_SIZE, GRID_SIZE),
    p=[0.15, 0.80, 0.05])

    return grid

# -------------------------
# NEIGHBORS
# -------------------------
def get_neighbors(grid, i, j):
    neighbors = []
    for x in range(max(0, i-1), min(GRID_SIZE, i+2)):
        for y in range(max(0, j-1), min(GRID_SIZE, j+2)):
            if (x, y) != (i, j):
                neighbors.append(grid[x, y])
    return neighbors

# -------------------------
# UPDATE RULES
# -------------------------
def update_cell(cell, neighbors, nutrients, oxygen):

    n_self = neighbors.count(SELF)
    n_diff = neighbors.count(DIFF)
    n_can = neighbors.count(CANCER)

    # -----------------
    # EMPTY SPACE
    # -----------------
    if cell == EMPTY:

        if n_can >= 3:
            return CANCER
        
        elif n_self >= 2:
            return SELF if np.random.rand() < 0.7 else DIFF

        else:
            return DIFF


    # -----------------
    # STEM CELLS
    # -----------------
    if cell == SELF:

        # environment stress increases death
        base_death = 0.02
        env_stress = (1 - nutrients)*0.2 + (1 - oxygen)*0.2
        death_prob = base_death + env_stress

        if np.random.rand() < death_prob:
            return EMPTY

        elif n_self >= 4: #overcrowding
            return DIFF if np.random.rand() < 0.9 else EMPTY
        
        return SELF
        

    # -----------------
    # DIFFERENTIATED CELLS
    # -----------------
    if cell == DIFF:

        base_death = 0.05
        env_stress = (1 - nutrients)*0.15 + (1 - oxygen)*0.15
        death_prob = base_death + env_stress

        if np.random.rand() < death_prob:
            return EMPTY

        return DIFF


    # -----------------
    # CANCER
    # -----------------
    if cell == CANCER:

        # cancer ignores environment
        if np.random.rand() < 0.01:
            return EMPTY

        return CANCER
    

# -------------------------
# STEP FUNCTION
# -------------------------
def step(grid, nutrients, oxygen):

    new_grid = grid.copy()

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):

            cell = grid[i, j]
            neighbors = get_neighbors(grid, i, j)

            new_grid[i, j] = update_cell(cell, neighbors, nutrients, oxygen)

    return new_grid



# ------------------------------------------------
# PLOT GRID
# ------------------------------------------------
def plot_grid(grid):

    cmap = ListedColormap([
        "black",   # empty / dead
        "green",   # differentiated
        "blue",    # stem / self-renew
        "purple"   # cancer
    ])

    fig, ax = plt.subplots(figsize=(6,6))

    ax.imshow(grid, cmap=cmap, vmin=0, vmax=3)

    ax.set_xticks([])
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    st.pyplot(fig, use_container_width=True)


# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(layout="wide")

st.markdown("""
<style>

/* Remove default padding */
.block-container {
    padding-top: 0.5rem;
    padding-bottom: 0rem;
}

/* Prevent page scrolling */
html, body, [data-testid="stAppViewContainer"] {
    height: 100vh;
    overflow: hidden;
}

/* Make main area fill screen */
[data-testid="stAppViewContainer"] > .main {
    height: 100vh;
}

/* Title styling */
h1 {
    font-size: 28px !important;
    margin-bottom: 0.3rem;
}

</style>
""", unsafe_allow_html=True)

st.title("🧬 Cell Fate Game – A Game Theory Simulation")


# ------------------------------------------------
# SIDEBAR CONTROLS
# ------------------------------------------------
st.sidebar.title("Game Controls")

st.sidebar.header("🌍 Environment")

nutrients = st.sidebar.slider(
    "Nutrient Level",
    min_value=0.0,
    max_value=1.0,
    value=0.6,
    step=0.05
)

oxygen = st.sidebar.slider(
    "Oxygen Level",
    min_value=0.0,
    max_value=1.0,
    value=0.6,
    step=0.05
)

st.sidebar.markdown("---")

st.sidebar.markdown("""
### 🎨 Legend

🟢 **Green** – Differentiated (stable tissue)  
🔵 **Blue** – Stem / Self-renew  
🟣 **Purple** – Cancer (cheater)  
⬛ **Black** – Dead / Empty
""")

st.sidebar.markdown("---")

st.sidebar.markdown("""
### 🧠 What to Observe

Balanced strategies → **stable tissue**

Too much proliferation → **tissue collapse**

Cancer cheats the rules and grows faster.

This illustrates **game theory in biological systems**.
""")


# ------------------------------------------------
# INITIALIZE GRID
# ------------------------------------------------
if "grid" not in st.session_state:
    st.session_state.grid = init_grid()


# ------------------------------------------------
# SIMULATION FUNCTIONS
# ------------------------------------------------
def run_steps(n_steps):

    for _ in range(n_steps):
        st.session_state.grid = step(
            st.session_state.grid,
            nutrients,
            oxygen
        )


def add_cancer_cells(n):

    for _ in range(n):
        x = np.random.randint(0, GRID_SIZE)
        y = np.random.randint(0, GRID_SIZE)

        if st.session_state.grid[x, y] != CANCER:
            st.session_state.grid[x, y] = CANCER


# ------------------------------------------------
# CONTROL BUTTONS
# ------------------------------------------------
col1, col2, col3 = st.columns(3)


# ---- Simulation control ----
with col1:

    st.subheader("Simulation")

    if st.button("▶ Next 10 Steps"):
        run_steps(10)

    if st.button("▶ Next 20 Steps"):
        run_steps(20)

    if st.button("▶ Next 50 Steps"):
        run_steps(50)


# ---- Cancer injection ----
with col2:

    st.subheader("Cancer Cells")

    if st.button("🟣 Add 10"):
        add_cancer_cells(10)

    if st.button("🟣 Add 20"):
        add_cancer_cells(20)

    if st.button("🟣 Add 50"):
        add_cancer_cells(50)


# ---- Reset ----
with col3:

    st.subheader("Reset")

    if st.button("🔄 Reset Grid"):
        st.session_state.grid = init_grid()


# ------------------------------------------------
# POPULATION STATISTICS
# ------------------------------------------------
unique, counts = np.unique(
    st.session_state.grid,
    return_counts=True
)

stats = dict(zip(unique, counts))

diff_cells = stats.get(DIFF, 0)
stem_cells = stats.get(SELF, 0)
empty_cells = stats.get(EMPTY, 0)
cancer_cells = stats.get(CANCER, 0)

st.markdown(
    f"""
### 📊 Population

🟢 Differentiated: **{diff_cells}**  
🔵 Stem Cells: **{stem_cells}**  
⬛ Empty: **{empty_cells}**  
🟣 Cancer: **{cancer_cells}**
"""
)


# ------------------------------------------------
# DISPLAY GRID
# ------------------------------------------------
plot_grid(st.session_state.grid)