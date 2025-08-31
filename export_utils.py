import os
import datetime
import html

def export_to_html(results, filename="results.html"):
    """
    Export test results to a styled HTML file with icons, colors, 
    print_ahead snippet, and expandable logs.
    """

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
    passed = sum(1 for r in results if r["result"] == "PASS")
    failed = sum(1 for r in results if r["result"] == "FAIL")
    summary_html = f"""
    <h2>Summary</h2>
    <p>Total: {total} | ✅ Pass: {passed} | ❌ Fail: {failed}</p>
    """

    # Build rows
    rows = ""
    for r in results:
        cls = r["result"].lower()
        icon = {"PASS": "✅", "FAIL": "❌", "RUNNING": "⏳", "PENDING": "➖"}.get(r["result"], "")
        
        # Extract print_ahead snippet
        snippet = ""
        found_text = r.get("found", "") or ""
        ahead = r.get("print_ahead_chars", "").strip()
        if ahead and ahead in found_text:
            idx = found_text.find(ahead)
            start = max(0, idx - 40)
            end = idx + len(ahead) + 40
            snippet = html.escape(found_text[start:end])
        elif ahead:
            snippet = f"(Not found: {ahead})"
        else:
            snippet = "(N/A)"

        # Escape values for HTML
        values = {k: html.escape(str(v)) for k,v in r.items()}

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
            <td><pre>{html.escape(found_text)}</pre></td>
            <td><pre>{snippet}</pre></td>
            <td class="icon">{icon} {values.get("result","")}</td>
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
                <th>Found</th>
                <th>Print Ahead Snippet</th>
                <th>Result</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename
