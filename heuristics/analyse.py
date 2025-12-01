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
    Returns a formatted markdown string or None.
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

    # Format output
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
        # Handle both 'Bin' objects and simple lists
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
    # Use standard matplotlib bar to avoid seaborn overhead for simple bars
    df.plot.bar(x="algorithm", y="bins_used", ax=axes[0], legend=False, title="Bins Used", color="skyblue", edgecolor="black")
    df.plot.bar(x="algorithm", y="pct_over_LB", ax=axes[1], legend=False, title="% Over Lower Bound", color="salmon", edgecolor="black")
    df.plot.bar(x="algorithm", y="time_sec", ax=axes[2], legend=False, title="Time (s)", color="lightgreen", edgecolor="black")
    plt.suptitle(f"{dataset_name} — Summary Comparison", fontsize=14)
    plt.tight_layout()
    plt.savefig(full_path, bbox_inches="tight")
    plt.close()
    return filename

# -------------------------------------------------------------
# Report Generator
# -------------------------------------------------------------
def generate_report(dataset_root=os.path.join(os.path.dirname(__file__), "..", "datasets")):
    report = StringIO()
    
    # Header
    report.write("# Bin Packing Heuristic Analysis Report\n\n")
    report.write("**Team Alan Turing**\n\n")
    report.write("Comparative analysis of First-Fit, Best-Fit, their Decreasing variants, and Harmonic-k.\n\n")
    report.write("---\n\n")

    # 1. PER-DATASET ANALYSIS
    report.write("## Part 1: Dataset-Level Analysis\n\n")
    
    for folder in sorted(os.listdir(dataset_root)):
        path = os.path.join(dataset_root, folder)
        if not os.path.isdir(path): continue

        items, capacity, weights = load_fsu_instance(path)
        lb = lower_bound(items, capacity)
        
        # Load Metadata (Source Info)
        meta_info = load_dataset_metadata(path)
        
        # Load Optimal Assignment
        opt_assignment = None
        try:
            opt_assignment = load_optimal_assignment(path)
        except Exception:
            pass

        report.write(f"### Dataset: {folder}\n")
        
        # Inject Metadata if available
        if meta_info:
            report.write(f"{meta_info}\n\n")
            
        report.write(f"**Items:** {len(items)} | **Capacity:** {capacity} | **Lower Bound:** {lb}\n\n")

        # --- Optimal Packing Visualization ---
        if opt_assignment:
            try:
                n_bins = max(opt_assignment)
                opt_bins = [[] for _ in range(n_bins)]
                for item, bin_idx in zip(items, opt_assignment):
                    # bin_idx is 1-based from file, convert to 0-based
                    opt_bins[bin_idx-1].append(item)
                
                img_name = f"{folder}_optimal.png"
                visualize_bins([type('Bin', (), {'items': b})() for b in opt_bins],
                               img_name, f"{folder} — Optimal Packing")
                
                report.write(f"#### Optimal Solution (Known)\n")
                report.write(f"![Optimal]({img_name})\n\n")
            except Exception as e:
                print(f"❌ [Error] Could not visualize optimal for '{folder}': {e}")

        # --- Run Heuristics ---
        dataset_rows = []
        for name, fn in ALGOS.items():
            # Run algo
            if name in ["FF", "BF"]:
                (bins_used, bins), t = timer(fn, items, 0)
            elif name == "Hk":
                (bins_used, bins), t = timer(fn, items) 
            else:
                (bins_used, bins), t = timer(fn, items) 
            
            # Metrics
            pct = pct_over_lb(bins_used, items)
            
            # Store for local chart
            dataset_rows.append({
                "algorithm": name,
                "bins_used": bins_used,
                "pct_over_LB": pct,
                "time_sec": round(t, 6),
            })
            
            # Generate Individual Bin Visualization
            img_name = f"{folder}_{name}.png"
            visualize_bins(bins, img_name, f"{folder} — {name}")
            
            # Write to Report
            report.write(f"**{name}** | Bins: {bins_used} (+{pct}%) | Time: {round(t, 5)}s\n\n")
            report.write(f"![{name}]({img_name})\n\n")

        # --- Local Summary Charts ---
        df_local = pd.DataFrame(dataset_rows)
        chart_name = plot_local_summary(df_local, folder)
        report.write(f"#### {folder} Performance Summary\n")
        report.write(f"![Summary]({chart_name})\n\n")
        report.write("---\n\n")

    # Save Markdown
    md_path = os.path.join(OUT_DIR, "analysis_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report.getvalue())

    print(f"✅ Markdown generated: {md_path}")
    return md_path

# -------------------------------------------------------------
# PDF / HTML Converter (Enhanced Styling)
# -------------------------------------------------------------
def convert_to_pdf(md_path):
    """
    Converts Markdown -> HTML -> PDF using WeasyPrint with
    Academic/Professional Styling.
    """
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 1. Convert Markdown to HTML
    html_content = markdown(md_text, extensions=['tables'])

    # 2. Advanced CSS Styling
    # Added max-height and object-fit: contain to img tag
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        @page {{
            margin: 2cm;
            size: A4;
            @top-right {{
                content: "Page " counter(page);
                font-family: 'Helvetica Neue', sans-serif;
                font-size: 9pt;
                color: #7f8c8d;
            }}
        }}
        
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
        }}

        /* Headers */
        h1 {{
            color: #2c3e50;
            font-size: 24pt;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        
        h2 {{
            color: #2980b9;
            font-size: 18pt;
            margin-top: 40px;
            border-left: 5px solid #2980b9;
            padding-left: 10px;
            page-break-after: avoid;
        }}
        
        h3 {{
            color: #7f8c8d;
            font-size: 14pt;
            margin-top: 25px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* Data Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 10pt;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        th {{
            background-color: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            border-bottom: 1px solid #ecf0f1;
            padding: 10px;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}

        /* Images and Charts */
        img {{
            max-width: 100%;
            width: auto;
            height: auto;
            max-height: 22cm; /* Fit within a single A4 page height */
            object-fit: contain; /* Scale down proportionally */
            margin: 20px auto;
            display: block;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            page-break-inside: avoid;
        }}
        
        /* Divider */
        hr {{
            border: 0;
            height: 1px;
            background: #bdc3c7;
            margin: 40px 0;
        }}
      </style>
    </head>
    <body>
    <div class="report-container">
        {html_content}
    </div>
    </body>
    </html>
    """

    # 3. Save HTML (for debugging/web view)
    html_path = md_path.replace(".md", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    # 4. Generate PDF
    pdf_path = md_path.replace(".md", ".pdf")
    print("⏳ Generating Professional PDF Report...")
    
    try:
        HTML(string=full_html, base_url=OUT_DIR).write_pdf(pdf_path)
        print(f"✅ PDF Report saved: {pdf_path}")
    except Exception as e:
        print(f"❌ PDF Generation Failed: {e}")
        print("   (Ensure GTK3/Cairo is installed. See README.md)")

if __name__ == "__main__":
    # Ensure we run from project root context
    report_md = generate_report()
    convert_to_pdf(report_md)