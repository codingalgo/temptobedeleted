import os
import datetime
import html
import webbrowser
import tkinter.messagebox as messagebox

def export_to_html(results, filename="results.html"):
    """
    Export test results to a styled HTML file with icons, colors,
    print_ahead snippet, and expandable logs.
    After saving, ask user if they want to open the report.
    """

    if not results:
        messagebox.showerror("No Results", "No results to export.")
        return None

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # CSS Styling
    css = """
    <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
    h1 { color: #343a40; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
    th, td { border: 1px solid #dee2e6; padding: 8px; text-align: left; }
    th { background-color: #343a40; color: white; }
    tr.pass { background-color: #d4edda; }
    tr.fail { background-color: #f8d7da; }
    tr.running { background-color: #fff3cd; }
    tr.pending { background-color: #e2e3e5; }
    tr:hover { background-color: #f1f1f1; }
    .icon { font-size: 18px; }
    details { margin-top: 5px; }
    pre { background: #f1f3f4; padding: 10px; border-radius: 5px; }
    </style>
    """

    # Summary counts
    total = len(results)
    passed = sum(1 for r in results if r.get("result") == "PASS")
    failed = sum(1 for r in results if r.get("result") == "FAIL")
    summary_html = f"""
    <h2>Summary</h2>
    <p>Total: {total} | ✅ Pass: {passed} | ❌ Fail: {failed}</p>
    """

    # Build rows
    rows = ""
    for r in results:
        res = r.get("result", "")
        cls = res.lower()
        icon = {"PASS": "✅", "FAIL": "❌", "RUNNING": "⏳", "PENDING": "➖"}.get(res, "")

        found_text = r.get("found", "") or ""
        after = r.get("print_after", "").strip()
        ahead = r.get("print_ahead_chars", "").strip()
        snippet = ""
        found_snippet = ""

        try:
            # Determine how many characters to capture
            n = int(r.get("n_chars", "50") or "50")  # Default 50 if not given

            # Snippet for Found column
            if after and after in found_text:
                idx = found_text.find(after) + len(after)
                found_snippet = found_text[idx: idx + n]
            elif ahead and ahead in found_text:
                idx = found_text.find(ahead)
                found_snippet = found_text[max(0, idx - n): idx + len(ahead) + n]
            else:
                found_snippet = found_text[:n]

            found_snippet = html.escape(found_snippet)

            # Print Ahead snippet (separate column)
            if ahead and ahead in found_text:
                idx = found_text.find(ahead)
                start = max(0, idx - 40)
                end = idx + len(ahead) + 40
                snippet = html.escape(found_text[start:end])
            elif ahead:
                snippet = f"(Not found: {html.escape(ahead)})"
            else:
                snippet = "(N/A)"

        except Exception:
            found_snippet = "(N/A)"
            snippet = "(N/A)"

        # Escape values for HTML
        values = {k: html.escape(str(v)) for k, v in r.items()}

        rows += f"""
        <tr class="{cls}">
            <td>{values.get("iteration","")}</td>
            <td>{values.get("command_name","")}</td>
            <td><pre>{values.get("command","")}</pre></td>
            <td>{values.get("expected","")}</td>
            <td>{values.get("regex","")}</td>
            <td>{values.get("negative","")}</td>
            <td>{values.get("wait_till","")}</td>
            <td>{values.get("print_after","")}</td>
            <td>{values.get("print_ahead_chars","")}</td>
            <td>{values.get("message","")}</td>
            <td>{values.get("retries","")}</td>
            <td><pre>{found_snippet}</pre></td>
            <td><pre>{snippet}</pre></td>
            <td class="icon">{icon} {res}</td>
        </tr>
        <tr><td colspan="14">
            <details><summary>View Full Logs</summary>
            <pre>{html.escape(found_text)}</pre>
            </details>
        </td></tr>
        """

    # Final HTML
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test Results</title>
        {css}
    </head>
    <body>
        <h1>Test Results</h1>
        <p>Generated: {now}</p>
        {summary_html}
        <table>
            <tr>
                <th>Iteration</th>
                <th>Command Name</th>
                <th>Command</th>
                <th>Expected</th>
                <th>Regex</th>
                <th>Negative</th>
                <th>Wait Till</th>
                <th>Print After</th>
                <th>Print Ahead</th>
                <th>Message</th>
                <th>Retries</th>
                <th>Found (substring)</th>
                <th>Print Ahead Snippet</th>
                <th>Result</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """

    # Save file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    abs_path = os.path.abspath(filename)
    messagebox.showinfo("Export Complete", f"Results exported to {abs_path}")

    # Ask user if they want to open it
    if messagebox.askyesno("Open Report", "Do you want to open the HTML report now?"):
        webbrowser.open(f"file://{abs_path}")

    return filename
