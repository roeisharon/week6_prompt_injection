"""
analyze_results.py — Results analysis and visualization.

Loads the filled results CSV (or sample data with --sample), computes Attack
Success Rates, produces five figures, saves a summary table, and prints key
findings to the console.

Usage
-----
    python analyze_results.py            # uses output/results/results_template.csv
    python analyze_results.py --sample   # uses output/results/results_sample.csv
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # non-interactive backend — no display required
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

import config

PALETTE   = {"white_text": "#2c7bb6", "tiny_font": "#d7191c"}
BEH_PAL   = {"banana": "#f4a442", "fake_citation": "#5b4fcf"}
LLM_PAL   = {"gpt5": "#10a37f", "gpt4o": "#10a37f", "claude": "#c05c2e"}
DPI       = 150
FONT_SIZE = 11
plt.rcParams.update({"font.size": FONT_SIZE, "axes.titlesize": FONT_SIZE + 2})

# Maps the 5 variant keys → 3 ordered strictness levels for progression plot
STRICTNESS_MAP = {
    "simple":               "simple",
    "markup_native_gpt4o":  "markup_native",
    "markup_native_claude": "markup_native",
    "strict_native_gpt4o":  "strict_native",
    "strict_native_claude": "strict_native",
}
STRICTNESS_ORDER = ["simple", "markup_native", "strict_native"]


def load_data(path: Path) -> pd.DataFrame:
    """Load results CSV, coerce success to float, drop unfilled rows."""
    df = pd.read_csv(path)

    df["success"] = (
        df["success"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"true": 1.0, "1": 1.0, "false": 0.0, "0": 0.0})
    )
    before = len(df)
    df = df.dropna(subset=["success"])
    dropped = before - len(df)
    if dropped:
        print(f"  Note: {dropped} rows dropped (empty success values)")

    df["success"] = df["success"].astype(float)
    df["strictness"] = df["variant"].map(STRICTNESS_MAP)
    return df


def fig1_heatmap(df: pd.DataFrame) -> None:
    """Heatmap of ASR by LLM (rows) × variant (columns)."""
    pivot = (
        df.groupby(["test_on_llm", "variant"])["success"]
        .mean()
        .unstack(fill_value=np.nan)
    )

    # Order columns: simple first, then markup, then strict
    col_order = [c for c in ["simple",
                              "markup_native_gpt4o", "markup_native_claude",
                              "strict_native_gpt4o", "strict_native_claude"]
                 if c in pivot.columns]
    pivot = pivot[col_order]

    fig, ax = plt.subplots(figsize=(10, 3.5))
    sns.heatmap(
        pivot,
        ax=ax,
        annot=True,
        fmt=".2f",
        cmap=sns.color_palette("Reds", as_cmap=True),
        vmin=0.0, vmax=1.0,
        linewidths=0.5,
        cbar_kws={"label": "ASR"},
    )
    ax.set_title("Attack Success Rate by LLM and Variant", pad=12)
    ax.set_xlabel("Variant")
    ax.set_ylabel("LLM")
    ax.tick_params(axis="x", rotation=25)
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    out = config.FIGURES_DIR / "asr_heatmap.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  Saved: {out}")


def fig2_technique_bar(df: pd.DataFrame) -> None:
    """Grouped bar chart: white_text vs tiny_font, grouped by LLM."""
    asr = (
        df.groupby(["test_on_llm", "technique"])["success"]
        .mean()
        .reset_index(name="asr")
    )

    llms       = asr["test_on_llm"].unique()
    techniques = ["white_text", "tiny_font"]
    x          = np.arange(len(llms))
    width      = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, tech in enumerate(techniques):
        vals = [
            asr.loc[(asr["test_on_llm"] == llm) & (asr["technique"] == tech), "asr"]
            .values[0] if len(asr.loc[(asr["test_on_llm"] == llm) & (asr["technique"] == tech)]) else 0
            for llm in llms
        ]
        bars = ax.bar(x + i * width - width / 2, vals, width,
                      label=tech, color=PALETTE[tech], alpha=0.85)
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=9)

    ax.set_title("Effect of Injection Technique on ASR", pad=10)
    ax.set_xlabel("LLM")
    ax.set_ylabel("Average ASR")
    ax.set_xticks(x)
    ax.set_xticklabels(llms)
    ax.set_ylim(0, 1.15)
    ax.legend(title="Technique")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = config.FIGURES_DIR / "technique_bar.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  Saved: {out}")


def fig3_variant_progression(df: pd.DataFrame) -> None:
    """Line chart of avg ASR across strictness levels."""
    asr = (
        df.groupby("strictness")["success"]
        .mean()
        .reindex(STRICTNESS_ORDER)
        .reset_index(name="asr")
    )

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(asr["strictness"], asr["asr"],
            marker="o", linewidth=2.5, color="#e63946", markersize=9)
    for _, row in asr.iterrows():
        ax.annotate(f"{row['asr']:.2f}",
                    (row["strictness"], row["asr"]),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=10)

    ax.set_title("ASR Progression Across Variant Strictness", pad=10)
    ax.set_xlabel("Variant Strictness Level")
    ax.set_ylabel("Average ASR (all models & behaviors)")
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = config.FIGURES_DIR / "variant_progression.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  Saved: {out}")


def fig4_behavior_bar(df: pd.DataFrame) -> None:
    """Grouped bar chart: banana vs fake_citation, grouped by LLM."""
    asr = (
        df.groupby(["test_on_llm", "behavior"])["success"]
        .mean()
        .reset_index(name="asr")
    )

    llms      = asr["test_on_llm"].unique()
    behaviors = ["banana", "fake_citation"]
    x         = np.arange(len(llms))
    width     = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, beh in enumerate(behaviors):
        vals = [
            asr.loc[(asr["test_on_llm"] == llm) & (asr["behavior"] == beh), "asr"]
            .values[0] if len(asr.loc[(asr["test_on_llm"] == llm) & (asr["behavior"] == beh)]) else 0
            for llm in llms
        ]
        bars = ax.bar(x + i * width - width / 2, vals, width,
                      label=beh, color=BEH_PAL[beh], alpha=0.85)
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=9)

    ax.set_title("ASR by Target Behavior and LLM", pad=10)
    ax.set_xlabel("LLM")
    ax.set_ylabel("Average ASR")
    ax.set_xticks(x)
    ax.set_xticklabels(llms)
    ax.set_ylim(0, 1.15)
    ax.legend(title="Behavior")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = config.FIGURES_DIR / "behavior_bar.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  Saved: {out}")


def fig5_per_pdf_bar(df: pd.DataFrame) -> None:
    """Bar chart of average ASR per source PDF."""
    asr = (
        df.groupby("pdf_id")["success"]
        .mean()
        .reset_index(name="asr")
        .sort_values("asr", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.bar(asr["pdf_id"], asr["asr"], color="#457b9d", alpha=0.85)
    ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=9)

    ax.set_title("ASR by Source Document", pad=10)
    ax.set_xlabel("Source PDF")
    ax.set_ylabel("Average ASR (all conditions)")
    ax.set_ylim(0, 1.15)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = config.FIGURES_DIR / "per_pdf_bar.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  Saved: {out}")


def save_summary_table(df: pd.DataFrame) -> None:
    """Save per-(technique, behavior, variant, llm) ASR table."""
    summary = (
        df.groupby(["technique", "behavior", "variant", "test_on_llm"])["success"]
        .agg(asr="mean", n_trials="count")
        .reset_index()
        .rename(columns={"test_on_llm": "llm"})
        .sort_values("asr", ascending=False)
    )
    out = config.RESULTS_DIR / "summary_table.csv"
    summary.to_csv(out, index=False)
    print(f"  Saved: {out}  ({len(summary)} rows)")


# ── Console key findings ──────────────────────────────────────────────────────

def print_key_findings(df: pd.DataFrame) -> None:
    """Print the KEY FINDINGS block to stdout."""

    def _asr(sub: pd.DataFrame) -> float:
        return sub["success"].mean() if len(sub) else float("nan")

    # Strongest combination: (variant, behavior, llm)
    combo = (
        df.groupby(["variant", "behavior", "test_on_llm"])["success"]
        .mean()
        .reset_index(name="asr")
        .sort_values("asr", ascending=False)
        .iloc[0]
    )

    # Per-LLM average
    llm_asr = df.groupby("test_on_llm")["success"].mean()
    most_vulnerable = llm_asr.idxmax()
    most_robust     = llm_asr.idxmin()

    # Strictness effect
    strict_asr = _asr(df[df["strictness"] == "strict_native"])
    simple_asr = _asr(df[df["strictness"] == "simple"])
    strictness_delta = strict_asr - simple_asr

    # Best behavior
    beh_asr  = df.groupby("behavior")["success"].mean()
    best_beh = beh_asr.idxmax()

    # Best technique
    tech_asr  = df.groupby("technique")["success"].mean()
    best_tech = tech_asr.idxmax()

    print("\nKEY FINDINGS")
    print("============")
    print(f"Strongest combination:   {combo['variant']} + {combo['behavior']} + "
          f"{combo['test_on_llm']} → ASR = {combo['asr']:.2f}")
    print(f"Most vulnerable LLM:     {most_vulnerable} "
          f"(avg ASR = {llm_asr[most_vulnerable]:.2f})")
    print(f"Most robust LLM:         {most_robust} "
          f"(avg ASR = {llm_asr[most_robust]:.2f})")
    print(f"Effect of strictness:    {strictness_delta:+.2f} ASR "
          f"(strict_native vs simple)")
    print(f"Best behavior:           {best_beh} "
          f"(avg ASR = {beh_asr[best_beh]:.2f})")
    print(f"Best technique:          {best_tech} "
          f"(avg ASR = {tech_asr[best_tech]:.2f})")
    print("Gemini finding:          Parser does not read injected text layer "
          "— ASR = 0.00")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    use_sample = "--sample" in sys.argv

    if use_sample:
        data_path = config.RESULTS_DIR / "results_sample.csv"
        print(f"\nLoading SAMPLE data: {data_path}")
    else:
        data_path = config.RESULTS_DIR / "results_template.csv"
        print(f"\nLoading results: {data_path}")

    if not data_path.exists():
        print(f"ERROR: {data_path} not found.")
        print("Run inject_pdf.py first, then evaluate_attacks.py.")
        sys.exit(1)

    df = load_data(data_path)

    if df.empty:
        print("No filled rows found. Fill in 'success' values and re-run.")
        sys.exit(1)

    print(f"  {len(df)} filled rows loaded.\n")
    print("Generating figures...")
    fig1_heatmap(df)
    fig2_technique_bar(df)
    fig3_variant_progression(df)
    fig4_behavior_bar(df)
    fig5_per_pdf_bar(df)

    print("\nSaving summary table...")
    save_summary_table(df)

    print_key_findings(df)
    print(f"\nAll outputs saved to {config.OUTPUT_DIR}\n")


if __name__ == "__main__":
    main()
