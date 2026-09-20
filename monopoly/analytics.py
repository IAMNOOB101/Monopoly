""" Functions to analyze the results of the simulation.
Includes statistical analysis and matplotlib/seaborn visualizations:
- Player survival rates with confidence intervals
- Game length distributions
- Net worth trajectories over turns
- Board landing frequency heatmap
- Gini coefficient for wealth inequality
"""

import os
import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend for headless environments
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

from monopoly.log_settings import LogSettings
from settings import SimulationSettings, GameSettings


# ── Board cell names for heatmap labels ─────────────────────
CELL_NAMES = [
    "GO", "Mediterranean", "Comm. Chest", "Baltic", "Income Tax",
    "Reading RR", "Oriental", "Chance", "Vermont", "Connecticut",
    "Jail", "St. Charles", "Electric Co.", "States", "Virginia",
    "Pennsylvania RR", "St. James", "Comm. Chest", "Tennessee", "New York",
    "Free Parking", "Kentucky", "Chance", "Indiana", "Illinois",
    "B&O RR", "Atlantic", "Ventnor", "Waterworks", "Marvin Gardens",
    "Go To Jail", "Pacific", "N. Carolina", "Comm. Chest", "Pennsylvania",
    "Short Line", "Chance", "Park Place", "Luxury Tax", "Boardwalk",
]

# Colors for each cell on the board
CELL_COLORS = [
    "#FFFFFF", "#8B4513", "#FFFFFF", "#8B4513", "#FFFFFF",
    "#000000", "#87CEEB", "#FFFFFF", "#87CEEB", "#87CEEB",
    "#FFFFFF", "#FF69B4", "#FFFFFF", "#FF69B4", "#FF69B4",
    "#000000", "#FFA500", "#FFFFFF", "#FFA500", "#FFA500",
    "#FFFFFF", "#FF0000", "#FFFFFF", "#FF0000", "#FF0000",
    "#000000", "#FFFF00", "#FFFF00", "#FFFFFF", "#FFFF00",
    "#FFFFFF", "#008000", "#008000", "#FFFFFF", "#008000",
    "#000000", "#FFFFFF", "#0000FF", "#FFFFFF", "#0000FF",
]


class Analyzer:
    """ Functions to analyze games after the simulation is finished
    data is read from the bankruptcies.tsv log file
    """

    def __init__(self):
        self.df = pd.read_csv(LogSettings.BANKRUPTCIES_PATH, sep='\t')
        self._networth_df = None
        self._landings_df = None

    @property
    def networth_df(self):
        """Lazy-load net worth data."""
        if self._networth_df is None:
            path = LogSettings.NETWORTH_LOG_PATH
            if os.path.exists(path) and os.path.getsize(path) > 50:
                try:
                    self._networth_df = pd.read_csv(path, sep='\t')
                except Exception:
                    self._networth_df = pd.DataFrame()
            else:
                self._networth_df = pd.DataFrame()
        return self._networth_df

    @property
    def landings_df(self):
        """Lazy-load landing data."""
        if self._landings_df is None:
            path = LogSettings.LANDINGS_LOG_PATH
            if os.path.exists(path) and os.path.getsize(path) > 50:
                try:
                    self._landings_df = pd.read_csv(path, sep='\t')
                except Exception:
                    self._landings_df = pd.DataFrame()
            else:
                self._landings_df = pd.DataFrame()
        return self._landings_df

    def run_all(self):
        """ Run all analysis functions """
        self.remaining_players()
        self.game_length()
        self.winning_rate()
        self.gini_coefficient()
        if HAS_PLOTTING:
            self.generate_plots()
        else:
            print("(matplotlib/seaborn not installed — skipping plot generation)")

    def remaining_players(self):
        """ number of games that had a clear winner, how many players remain at the end
        """
        grouped = self.df.groupby('game_number').size().reset_index(name='Losers')
        result = grouped['Losers'].value_counts().reset_index()
        result.columns = ['Losers', 'count']

        # {remaining players: games}
        remaining_players = {len(GameSettings.players_list) - row['Losers']: row['count'] for index, row in
                             result.iterrows()}
        # Add games with no losers (all players remained)
        remaining_players[len(GameSettings.players_list)] = \
            SimulationSettings.n_games - sum(remaining_players.values())

        # Games with a clear winner (just a single player remains)
        clear_winner = 0
        if 1 in remaining_players:
            clear_winner = remaining_players[1]
        print(f"Games that had clear winner: {clear_winner} / {SimulationSettings.n_games} " +
              f"({100 * clear_winner / SimulationSettings.n_games:.1f}%)")

        # Number of players by the end of simulation
        print(f"Number of remaining players after: {SimulationSettings.n_moves} turns:")
        for remaining, count in sorted(remaining_players.items()):
            print(f"  - {remaining}: {count} ({count * 100 / SimulationSettings.n_games:.1f}%)")

    def game_length(self):
        """ Median game length (for all finite games)
        """
        # Calculate median game length, which is the highest bankruptcy turn within a game
        grouped = self.df.groupby('game_number')
        filtered_groups = grouped.filter(lambda x: len(x) == len(GameSettings.players_list) - 1)
        lengths_df = filtered_groups.groupby('game_number')['turn'].max().reset_index()
        lengths = sorted(lengths_df["turn"].tolist())
        all_lengths = lengths + [SimulationSettings.n_moves
                                 for _ in range(SimulationSettings.n_games - len(lengths))]
        if lengths:
            print(f"Median game length (for finished games): {lengths[len(lengths) // 2]}")
        print(f"Median game length (for all games): {all_lengths[len(all_lengths) // 2]}")

        # Calculate average survival time (for those who goes bankrupt)
        survival_average = lengths_df["turn"].mean()
        print(f"Average survival time (for bankrupt players): {survival_average:.1f} turns")

    def winning_rate(self):
        """ Display winning (survival) rate of players
        """
        loses_counts = self.df.groupby('player_bankrupt').size().reset_index(name='count')

        # {player: games_survived}
        loses_dict = {row['player_bankrupt']: row['count'] for index, row in loses_counts.iterrows()}
        print("Players' survival rate:")

        for player in GameSettings.players_list:
            player_name = player[0]
            loses = loses_dict.get(player_name, 0)
            survivals = SimulationSettings.n_games - loses

            survival_rate = survivals / SimulationSettings.n_games
            margin = 1.96 * (survival_rate * (1 - survival_rate) / SimulationSettings.n_games) ** 0.5
            print(f"  - {player_name}: {survivals} " +
                  f"({survival_rate * 100:.1f} "
                  f"+- {margin * 100:.1f}%)")

    def gini_coefficient(self):
        """Calculate and display the Gini coefficient of final net worths.
        Higher Gini = more wealth inequality = more decisive games.
        """
        if self.networth_df.empty:
            print("Gini coefficient: (no net worth data available)")
            return

        # Get the last recorded net worth for each player in each game
        last_nw = self.networth_df.groupby(['game_number', 'player']).last().reset_index()

        if 'net_worth' not in last_nw.columns:
            print("Gini coefficient: (net worth column not found)")
            return

        gini_values = []
        for game_num, group in last_nw.groupby('game_number'):
            values = sorted(group['net_worth'].values)
            n = len(values)
            if n < 2 or sum(values) == 0:
                continue
            # Gini formula
            index_sum = sum((i + 1) * v for i, v in enumerate(values))
            gini = (2 * index_sum) / (n * sum(values)) - (n + 1) / n
            gini_values.append(gini)

        if gini_values:
            avg_gini = np.mean(gini_values)
            print(f"Average Gini coefficient (wealth inequality): {avg_gini:.3f}")
            print(f"  (0 = perfect equality, 1 = one player owns everything)")
        else:
            print("Gini coefficient: insufficient data")

    # ── Visualization ───────────────────────────────────────

    def generate_plots(self):
        """Generate all visualization plots and save to the plots directory."""
        plots_dir = LogSettings.PLOTS_DIR
        plots_dir.mkdir(exist_ok=True)

        print(f"\nGenerating plots in {plots_dir}/ ...")

        self._plot_game_length_distribution(plots_dir)
        self._plot_survival_rates(plots_dir)
        self._plot_net_worth_trajectories(plots_dir)
        self._plot_landing_heatmap(plots_dir)

        print("Plot generation complete.")

    def _plot_game_length_distribution(self, plots_dir):
        """Histogram of game lengths (turns until winner is determined)."""
        grouped = self.df.groupby('game_number')
        filtered = grouped.filter(lambda x: len(x) == len(GameSettings.players_list) - 1)
        if filtered.empty:
            print("  - Skipping game length histogram (no finished games)")
            return

        lengths = filtered.groupby('game_number')['turn'].max().values

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(lengths, bins=40, kde=True, color='#4A90D9', edgecolor='white', ax=ax)
        ax.set_title('Game Length Distribution', fontsize=16, fontweight='bold')
        ax.set_xlabel('Turns to Complete', fontsize=12)
        ax.set_ylabel('Number of Games', fontsize=12)

        # Add median line
        median_len = int(np.median(lengths))
        ax.axvline(median_len, color='#E74C3C', linestyle='--', linewidth=2,
                   label=f'Median: {median_len} turns')
        ax.legend(fontsize=11)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()
        fig.savefig(plots_dir / "game_length_distribution.png", dpi=150)
        plt.close(fig)
        print("  - game_length_distribution.png")

    def _plot_survival_rates(self, plots_dir):
        """Bar chart of player survival rates with confidence intervals."""
        loses_counts = self.df.groupby('player_bankrupt').size().reset_index(name='count')
        loses_dict = {row['player_bankrupt']: row['count'] for _, row in loses_counts.iterrows()}

        names = []
        rates = []
        margins = []
        for player in GameSettings.players_list:
            player_name = player[0]
            loses = loses_dict.get(player_name, 0)
            survivals = SimulationSettings.n_games - loses
            rate = survivals / SimulationSettings.n_games
            margin = 1.96 * (rate * (1 - rate) / SimulationSettings.n_games) ** 0.5
            names.append(player_name)
            rates.append(rate * 100)
            margins.append(margin * 100)

        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12']
        bars = ax.bar(names, rates, yerr=margins, capsize=8,
                      color=colors[:len(names)], edgecolor='white', linewidth=1.5,
                      error_kw={'linewidth': 2, 'color': '#333'})
        ax.set_title('Player Survival Rates', fontsize=16, fontweight='bold')
        ax.set_ylabel('Survival Rate (%)', fontsize=12)
        ax.set_ylim(0, 105)

        # Add value labels
        for bar, rate, margin in zip(bars, rates, margins):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + margin + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()
        fig.savefig(plots_dir / "survival_rates.png", dpi=150)
        plt.close(fig)
        print("  - survival_rates.png")

    def _plot_net_worth_trajectories(self, plots_dir):
        """Line plot showing average net worth over turns for each player."""
        if self.networth_df.empty:
            print("  - Skipping net worth trajectories (no data)")
            return

        fig, ax = plt.subplots(figsize=(12, 6))
        colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12']

        # Average net worth per player per turn across all games
        avg_nw = self.networth_df.groupby(['turn', 'player'])['net_worth'].mean().reset_index()

        player_names = avg_nw['player'].unique()
        for i, player_name in enumerate(player_names):
            player_data = avg_nw[avg_nw['player'] == player_name]
            color = colors[i % len(colors)]
            ax.plot(player_data['turn'], player_data['net_worth'],
                    label=player_name, color=color, linewidth=2, alpha=0.85)

        ax.set_title('Average Net Worth Over Time', fontsize=16, fontweight='bold')
        ax.set_xlabel('Turn', fontsize=12)
        ax.set_ylabel('Net Worth ($)', fontsize=12)
        ax.legend(fontsize=11, loc='upper left')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3)
        fig.tight_layout()
        fig.savefig(plots_dir / "net_worth_trajectories.png", dpi=150)
        plt.close(fig)
        print("  - net_worth_trajectories.png")

    def _plot_landing_heatmap(self, plots_dir):
        """Heatmap showing landing frequency for each board position."""
        if self.landings_df.empty:
            print("  - Skipping landing heatmap (no data)")
            return

        # Count landings per position
        counts = self.landings_df['position'].value_counts().sort_index()
        all_counts = [counts.get(i, 0) for i in range(40)]
        total = sum(all_counts)
        if total == 0:
            print("  - Skipping landing heatmap (no landing data)")
            return
        frequencies = [c / total * 100 for c in all_counts]

        fig, ax = plt.subplots(figsize=(16, 6))
        bar_colors = []
        for i, freq in enumerate(frequencies):
            # Color intensity based on frequency
            intensity = min(freq / max(frequencies), 1.0) if max(frequencies) > 0 else 0
            r = int(255 * (1 - intensity) + 74 * intensity)
            g = int(255 * (1 - intensity) + 144 * intensity)
            b = int(255 * (1 - intensity) + 217 * intensity)
            bar_colors.append(f'#{r:02x}{g:02x}{b:02x}')

        bars = ax.bar(range(40), frequencies, color=bar_colors, edgecolor='#666', linewidth=0.5)

        ax.set_title('Board Landing Frequency', fontsize=16, fontweight='bold')
        ax.set_xlabel('Board Position', fontsize=12)
        ax.set_ylabel('Landing Frequency (%)', fontsize=12)
        ax.set_xticks(range(40))
        ax.set_xticklabels(CELL_NAMES, rotation=90, fontsize=7)

        # Highlight top 5
        top5 = sorted(range(40), key=lambda i: frequencies[i], reverse=True)[:5]
        for idx in top5:
            bars[idx].set_edgecolor('#E74C3C')
            bars[idx].set_linewidth(2)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()
        fig.savefig(plots_dir / "landing_frequency.png", dpi=150)
        plt.close(fig)
        print("  - landing_frequency.png")
