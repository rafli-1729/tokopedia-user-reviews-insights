import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.cm as cm
import numpy as np

def plot_rating_distribution(df, title, ax_pie, ax_bar):
    rating_counts = df.rating.value_counts().sort_index()

    # Color palette
    cmap = cm.get_cmap("summer")
    norm = (rating_counts.index - rating_counts.index.min()) / (rating_counts.index.max() - rating_counts.index.min())
    pie_colors = [cmap(v) for v in norm][::-1]

    # Pie Chart
    wedges, _ = ax_pie.pie(
        rating_counts.values, startangle=90, colors=pie_colors, labels=None,
        wedgeprops={'edgecolor': 'black', 'linewidth': 0.5}
    )

    # percentages
    for i, w in enumerate(wedges):
        ang = (w.theta2 + w.theta1) / 2
        x = 1.20 * np.cos(np.deg2rad(ang))
        y = 1.20 * np.sin(np.deg2rad(ang))
        percent = rating_counts.values[i] / rating_counts.sum() * 100

        ax_pie.text(
            x, y, f"{percent:.1f}%", ha="center", va="center",
            fontsize=12, weight="bold", color="#1F2937"
        )

    legend_labels = [f"Rating {idx}" for idx in rating_counts.index]
    ax_pie.legend(
        wedges, legend_labels, title="Legend",
        loc="center left", bbox_to_anchor=(0.85, 0.5), fontsize=9
    )
    ax_pie.axis("equal")

    # Bar Chart
    bars = ax_bar.barh(
        rating_counts.index, rating_counts.values,
        color=pie_colors, edgecolor="#333333"
    )

    ax_bar.set_xlabel("Counts")
    ax_bar.set_ylabel("Rating")

    # annotate bar values
    for bar in bars:
        x = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        ax_bar.text(
            x + max(rating_counts.values) * 0.02, y,
            f"{int(x):,}",
            ha="left", va="center", fontsize=11, weight="bold"
        )

    ax_bar.margins(x=0.2)


def compare_length_distribution(datasets):
    fig, axes = plt.subplots(1, len(datasets), figsize=(22, 6), sharey=True)

    for ax, (title, data, color) in zip(axes, datasets):
        sns.histplot(
            data,
            bins=100,
            kde=True,
            edgecolor='black',
            color=color,
            ax=ax
        )

        ax.set_title(f"{title} Text Length Distribution", fontsize=16, weight="bold")
        ax.set_xlabel("Length (characters)")
        ax.set_ylabel("Frequency")

    plt.tight_layout()
    plt.show()