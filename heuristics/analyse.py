# heuristics/analyse.py
"""
Automatic Bin Packing Analysis Report Generator
-----------------------------------------------
Generates:
1. Markdown Report (.md)
2. HTML Report (.html)
3. PDF Report (.pdf) via WeasyPrint

Includes Individual Theoretical Validation Graphs.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import StringIO
from markdown import markdown
from weasyprint import HTML, CSS

# Import your heuristics
from heuristics.util import load_fsu_instance, load_optimal_assignment, pct_over_lb, timer, lower_bound
from heuristics.firstfit.ff import run_ff
from heuristics.bestfit.bf import run_bf
from heuristics.firstfitdecreasing.ffd import run_ffd
from heuristics.bestfitdecreasing.bfd import run_bfd
from heuristics.harmonic.hk import run_hk

ALGOS = {
    "FF": run_ff,
    "BF": run_bf,
    "FFD": run_ffd,
    "BFD": run_bfd,
    "Hk": run_hk,
}

OUT_DIR = "analysis_output"
os.makedirs(OUT_DIR, exist_ok=True)

# -------------------------------------------------------------
# Metadata Loader
# -------------------------------------------------------------
def load_dataset_metadata(folder_path):
    """
    Reads 'source.txt' if present and extracts Category/Original File.
    """
    source_file = os.path.join(folder_path, "source.txt")
    if not os.path.exists(source_file):
        return None
        
    metadata = {}
    try:
        with open(source_file, "r") as f:
            for line in f:
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip().lower()] = val.strip()
    except Exception:
        return None

    category = metadata.get("category", "Unknown")
    orig_file = metadata.get("original file", "Unknown")
    return f"**Category:** {category} &nbsp;|&nbsp; **Source:** `{orig_file}`"

# -------------------------------------------------------------
# Visualization Helpers
# -------------------------------------------------------------
def visualize_bins(bins, filename, title):
    """Generates a bar chart of the bin layout."""
    full_path = os.path.join(OUT_DIR, filename)
    plt.figure(figsize=(6, 0.6 * len(bins) + 1))
    for i, b in enumerate(bins):
        left = 0.0
        items = b.items if hasattr(b, 'items') else b
        for item in items:
            plt.barh(y=i, width=item, left=left, edgecolor="black")
            left += item
        if left < 1.0:
            plt.barh(y=i, width=1-left, left=left, color="lightgray", alpha=0.2)
    plt.yticks(range(len(bins)), [f"Bin {i+1}" for i in range(len(bins))])
    plt.xlabel("Bin Capacity (normalized)")
    plt.title(title)
    plt.xlim(0, 1)
    plt.tight_layout()
    plt.savefig(full_path, bbox_inches="tight")
    plt.close()

def plot_local_summary(df, dataset_name):
    """Generates summary comparison charts for a SINGLE dataset."""
    filename = f"{dataset_name}_summary.png"
    full_path = os.path.join(OUT_DIR, filename)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    df.plot.bar(x="algorithm", y="bins_used", ax=axes[0], legend=False, title="Bins Used", color="skyblue", edgecolor="black")
    df.plot.bar(x="algorithm", y="pct_over_LB", ax=axes[1], legend=False, title="% Over Lower Bound", color="salmon", edgecolor="black")
    df.plot.bar(x="algorithm", y="time_sec", ax=axes[2], legend=False, title="Time (s)", color="lightgreen", edgecolor="black")
    plt.suptitle(f"{dataset_name} — Summary Comparison", fontsize=14)
    plt.tight_layout()
    plt.savefig(full_path, bbox_inches="tight")
    plt.close()
    return filename

def plot_algorithm_validation(df):
    """
    Generates 5 separate line graphs (one per algorithm) comparing
    Actual Bins Used vs Theoretical Upper Bound PER TEST CASE.
    
    Theoretical bounds:
    - FF/BF: 1.7 × OPT
    - FFD/BFD: (11/9) × OPT ≈ 1.222 × OPT
    - Hk: 1.691 × OPT
    
    Returns a dictionary of {algo_name: filename}.
    """
    # Theoretical Multipliers (based on optimal solution)
    factors = {
        "FF": 1.7,
        "BF": 1.7,
        "FFD": 11.0/9.0,
        "BFD": 11.0/9.0,
        "Hk": 1.691
    }
    
    generated_files = {}
    
    for algo, factor in factors.items():
        # Filter data for this algorithm
        subset = df[df['algorithm'] == algo].copy()
        if subset.empty: 
            continue
        
        # Sort by dataset name for consistent x-axis
        subset = subset.sort_values('dataset').reset_index(drop=True)
        
        # Calculate theoretical bound for EACH test case
        # Theoretical Bound = factor × optimal_bins (for that specific test case)
        subset['theoretical_bound'] = subset['optimal_bins'] * factor
        
        # Create the plot
        filename = f"validation_{algo}.png"
        full_path = os.path.join(OUT_DIR, filename)
        
        plt.figure(figsize=(12, 6))
        
        # X-axis: numeric indices for proper line plotting
        x_indices = np.arange(len(subset))
        
        # Plot 1: Actual Bins Used by the algorithm (blue line)
        plt.plot(
            x_indices,
            subset['bins_used'], 
            marker='o', 
            label=f'{algo} Actual Bins Used', 
            color='tab:blue',
            linewidth=2.5,
            markersize=8
        )
        
        # Plot 2: Theoretical Upper Bound per test case (red dashed line)
        plt.plot(
            x_indices,
            subset['theoretical_bound'], 
            marker='X', 
            label=f'Theoretical Bound ({factor:.3f} × OPT)', 
            color='tab:red',
            linestyle='--',
            linewidth=2,
            markersize=8
        )
        
        # Formatting
        plt.xticks(x_indices, subset['dataset'], rotation=45, ha='right')
        plt.title(f"{algo}: Actual Performance vs Theoretical Upper Bound", fontsize=14, fontweight='bold')
        plt.ylabel("Number of Bins", fontsize=12)
        plt.xlabel("Dataset (Test Case)", fontsize=12)
        plt.legend(loc='best', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save
        plt.savefig(full_path, bbox_inches="tight", dpi=150)
        plt.close()
        
        generated_files[algo] = filename
        
    return generated_files

# -------------------------------------------------------------
# Report Generator
# -------------------------------------------------------------
def generate_report(dataset_root=os.path.join(os.path.dirname(__file__), "..", "datasets")):
    report = StringIO()
    report.write("# Bin Packing Heuristic Analysis Report\n\n")
    report.write("**Team Alan Turing**\n\n")
    report.write("Comparative analysis of First-Fit, Best-Fit, their Decreasing variants, and Harmonic-k.\n\n")
    report.write("---\n\n")

    report.write("## Part 1: Dataset-Level Analysis\n\n")
    
    # Global collection for validation graphs
    all_stats = []

    for folder in sorted(os.listdir(dataset_root)):
        path = os.path.join(dataset_root, folder)
        if not os.path.isdir(path): 
            continue

        items, capacity, weights = load_fsu_instance(path)
        lb = lower_bound(items, capacity)
        meta_info = load_dataset_metadata(path)
        
        # Load optimal assignment and extract optimal bin count
        opt_assignment = None
        optimal_bins = None
        try:
            opt_assignment = load_optimal_assignment(path)
            if opt_assignment:
                optimal_bins = max(opt_assignment)  # Actual optimal bin count
        except Exception:
            pass
        
        # If no optimal found, use lower bound as fallback
        if optimal_bins is None:
            optimal_bins = lb

        report.write(f"### Dataset: {folder}\n")
        if meta_info: 
            report.write(f"{meta_info}\n\n")
        report.write(f"**Items:** {len(items)} | **Capacity:** {capacity} | **Lower Bound:** {lb}")
        if opt_assignment:
            report.write(f" | **Optimal:** {optimal_bins}")
        report.write("\n\n")

        # Visualize optimal solution if available
        if opt_assignment:
            try:
                n_bins = max(opt_assignment)
                opt_bins = [[] for _ in range(n_bins)]
                for item, bin_idx in zip(items, opt_assignment):
                    opt_bins[bin_idx-1].append(item)
                img_name = f"{folder}_optimal.png"
                visualize_bins([type('Bin', (), {'items': b})() for b in opt_bins],
                               img_name, f"{folder} — Optimal Packing")
                report.write(f"#### Optimal Solution\n")
                report.write(f"![Optimal]({img_name})\n\n")
            except Exception as e:
                print(f"❌ [Error] {folder} Optimal Vis Failed: {e}")

        # Run all algorithms
        dataset_rows = []
        for name, fn in ALGOS.items():
            if name in ["FF", "BF"]:
                (bins_used, bins), t = timer(fn, items, 0)
            elif name == "Hk":
                (bins_used, bins), t = timer(fn, items) 
            else:
                (bins_used, bins), t = timer(fn, items) 
            
            pct = pct_over_lb(bins_used, items)
            
            # Store for local summary
            dataset_rows.append({
                "algorithm": name,
                "bins_used": bins_used,
                "pct_over_LB": pct,
                "time_sec": round(t, 6),
            })
            
            # Store for global validation graphs
            all_stats.append({
                "dataset": folder,
                "algorithm": name,
                "bins_used": bins_used,
                "optimal_bins": optimal_bins  # Optimal for THIS test case
            })
            
            # Visualize algorithm result
            img_name = f"{folder}_{name}.png"
            visualize_bins(bins, img_name, f"{folder} — {name}")
            report.write(f"**{name}** | Bins: {bins_used} (+{pct}%) | Time: {round(t, 5)}s\n\n")
            report.write(f"![{name}]({img_name})\n\n")

        # Local summary chart
        df_local = pd.DataFrame(dataset_rows)
        chart_name = plot_local_summary(df_local, folder)
        report.write(f"#### {folder} Performance Summary\n")
        report.write(f"![Summary]({chart_name})\n\n")
        report.write("---\n\n")

    # --- PART 2: THEORETICAL VALIDATION GRAPHS ---
    if all_stats:
        df_all = pd.DataFrame(all_stats)
        
        report.write("## Part 2: Theoretical Validation\n\n")
        report.write("The following graphs compare the actual number of bins used by each algorithm ")
        report.write("against its theoretical worst-case upper bound **for each test case**.\n\n")
        report.write("- **Blue Line:** Actual bins used by the algorithm.\n")
        report.write("- **Red Dashed Line:** Theoretical upper bound (factor × optimal) for that test case.\n\n")
        report.write("**Theoretical Bounds:**\n")
        report.write("- FF/BF: 1.7 × OPT\n")
        report.write("- FFD/BFD: (11/9) × OPT ≈ 1.222 × OPT\n")
        report.write("- Harmonic-k: 1.691 × OPT\n\n")
        
        # Generate validation plots
        validation_plots = plot_algorithm_validation(df_all)
        
        for algo_name, filename in validation_plots.items():
            report.write(f"### {algo_name} Validation\n")
            report.write(f"![{algo_name} Validation]({filename})\n\n")

    # Save Markdown
    md_path = os.path.join(OUT_DIR, "analysis_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report.getvalue())
    
    print(f"✅ Markdown generated: {md_path}")
    return md_path

# -------------------------------------------------------------
# PDF / HTML Converter
# -------------------------------------------------------------
def convert_to_pdf(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    html_content = markdown(md_text, extensions=['tables'])

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        @page {{ margin: 2cm; size: A4; @top-right {{ content: "Page " counter(page); font-family: sans-serif; font-size: 9pt; color: #7f8c8d; }} }}
        body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #333; }}
        h1 {{ color: #2c3e50; font-size: 24pt; border-bottom: 3px solid #3498db; margin-top: 0; }}
        h2 {{ color: #2980b9; font-size: 18pt; margin-top: 40px; border-left: 5px solid #2980b9; padding-left: 10px; page-break-after: avoid; }}
        h3 {{ color: #7f8c8d; font-size: 14pt; margin-top: 25px; text-transform: uppercase; letter-spacing: 1px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 10pt; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th {{ background-color: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ border-bottom: 1px solid #ecf0f1; padding: 10px; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        img {{ max-width: 100%; width: auto; height: auto; max-height: 22cm; object-fit: contain; margin: 20px auto; display: block; border: 1px solid #bdc3c7; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); page-break-inside: avoid; }}
        hr {{ border: 0; height: 1px; background: #bdc3c7; margin: 40px 0; }}
      </style>
    </head>
    <body>
    <div class="report-container">{html_content}</div>
    </body>
    </html>
    """

    html_path = md_path.replace(".md", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    pdf_path = md_path.replace(".md", ".pdf")
    print("⏳ Generating Professional PDF Report...")
    try:
        HTML(string=full_html, base_url=OUT_DIR).write_pdf(pdf_path)
        print(f"✅ PDF Report saved: {pdf_path}")
    except Exception as e:
        print(f"❌ PDF Generation Failed: {e}")

if __name__ == "__main__":
    report_md = generate_report()
    convert_to_pdf(report_md)