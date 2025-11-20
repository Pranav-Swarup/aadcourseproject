# heuristics/analyse.py
"""
Automatic Bin Packing Analysis Report Generator
-----------------------------------------------
Generates:
1. Markdown Report (.md)
2. HTML Report (.html)
3. PDF Report (.pdf) via WeasyPrint
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
from markdown import markdown
from weasyprint import HTML, CSS

# Import your heuristics
from heuristics.util import load_fsu_instance, load_optimal_assignment, pct_over_lb, timer
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
# Visualization Helpers
# -------------------------------------------------------------
def visualize_bins(bins, filename, title):
    """Generates a bar chart of the bin layout."""
    # Save FULL path for file writing
    full_path = os.path.join(OUT_DIR, filename)
    
    plt.figure(figsize=(6, 0.6 * len(bins) + 1))
    for i, b in enumerate(bins):
        left = 0.0
        # Handle both 'Bin' objects and simple lists if necessary
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

def plot_summary(df, dataset_name):
    """Generates summary comparison charts."""
    filename = f"{dataset_name}_summary.png"
    full_path = os.path.join(OUT_DIR, filename)
    
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    df.plot.bar(x="algorithm", y="bins_used", ax=axes[0], legend=False, title="Bins Used")
    df.plot.bar(x="algorithm", y="pct_over_LB", ax=axes[1], legend=False, title="% Over Lower Bound")
    df.plot.bar(x="algorithm", y="time_sec", ax=axes[2], legend=False, title="Time (s)")
    plt.suptitle(f"{dataset_name} — Summary Comparison", fontsize=14)
    plt.tight_layout()
    plt.savefig(full_path, bbox_inches="tight")
    plt.close()
    return filename # Return only filename for MD linkage

# -------------------------------------------------------------
# Report Generator
# -------------------------------------------------------------
def generate_report(dataset_root=os.path.join(os.path.dirname(__file__), "..", "datasets")):
    report = StringIO()
    report.write("# Bin Packing Heuristic Analysis Report\n\n")
    report.write("Comparative analysis of First-Fit, Best-Fit, their Decreasing variants, and Harmonic-k.\n\n")

    for folder in sorted(os.listdir(dataset_root)):
        path = os.path.join(dataset_root, folder)
        if not os.path.isdir(path): continue

        items, capacity, weights = load_fsu_instance(path)
        opt_assignment = load_optimal_assignment(path)
        
        report.write(f"## Dataset: {folder}\n")
        report.write(f"**Items:** {len(items)} | **Capacity:** {capacity}\n\n")

        # --- Optimal Packing Visualization ---
        if opt_assignment:
            n_bins = max(opt_assignment)
            opt_bins = [[] for _ in range(n_bins)]
            for item, bin_idx in zip(items, opt_assignment):
                opt_bins[bin_idx-1].append(item)
            
            img_name = f"{folder}_optimal.png"
            visualize_bins([type('Bin', (), {'items': b})() for b in opt_bins],
                           img_name, f"{folder} — Optimal Packing")
            
            report.write(f"### Optimal Solution\n")
            report.write(f"![Optimal]({img_name})\n\n")

        # --- Run Heuristics ---
        dataset_rows = []
        for name, fn in ALGOS.items():
            # Run algo
            if name in ["FF", "BF"]:
                (bins_used, bins), t = timer(fn, items, 0)
            elif name == "Hk":
                (bins_used, bins), t = timer(fn, items) # Harmonic doesn't need flag
            else:
                (bins_used, bins), t = timer(fn, items) # FFD/BFD might need flags depending on implementation
                
            dataset_rows.append({
                "algorithm": name,
                "bins_used": bins_used,
                "pct_over_LB": pct_over_lb(bins_used, items),
                "time_sec": round(t, 6),
            })
            
            # Generate Image
            img_name = f"{folder}_{name}.png"
            visualize_bins(bins, img_name, f"{folder} — {name}")
            
            # Write to Report (Use filename ONLY, not full path)
            report.write(f"**{name}** | Bins: {bins_used} | Time: {round(t, 5)}s\n\n")
            report.write(f"![{name}]({img_name})\n\n")

        # --- Summary Charts ---
        df_local = pd.DataFrame(dataset_rows)
        chart_name = plot_summary(df_local, folder)
        report.write(f"### {folder} Summary\n")
        report.write(f"![Summary]({chart_name})\n\n")
        report.write("---\n\n")

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
    """
    Converts Markdown -> HTML -> PDF using WeasyPrint.
    """
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 1. Convert Markdown to HTML
    html_content = markdown(md_text, extensions=['tables'])

    # 2. Wrap in nice CSS
    full_html = f"""
    <html>
    <head>
      <style>
        @page {{ margin: 1in; size: A4; }}
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; font-size: 12px; line-height: 1.5; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
        h2 {{ color: #e67e22; margin-top: 30px; page-break-after: avoid; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; }}
        img {{ max-width: 100%; height: auto; margin: 10px 0; border: 1px solid #eee; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        hr {{ border: 0; border-top: 1px solid #eee; margin: 30px 0; page-break-after: always; }}
      </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """

    # 3. Save HTML (for debugging)
    html_path = md_path.replace(".md", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    # 4. Generate PDF
    # base_url=OUT_DIR tells WeasyPrint where to look for the images (e.g. "p01_FF.png")
    pdf_path = md_path.replace(".md", ".pdf")
    print("⏳ Generating PDF (this may take a moment)...")
    
    HTML(string=full_html, base_url=OUT_DIR).write_pdf(pdf_path)

    print(f"✅ PDF Report saved: {pdf_path}")

if __name__ == "__main__":
    # Ensure we run from project root context
    report_md = generate_report()
    convert_to_pdf(report_md)