import datetime, webbrowser


def export_to_html(results, filename="results.html"):
    total = len(results)
    passed = sum(1 for r in results if r.get("result") == "PASS")
    failed = sum(1 for r in results if r.get("result") == "FAIL")
    iterations = max((r.get("iteration", 1) for r in results), default=1)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<html><head><title>Test Results</title>")
        f.write("<style>")
        f.write("body{font-family:Arial;margin:20px;} th,td{border:1px solid #ccc;padding:6px;font-size:13px;}")
        f.write("table{border-collapse:collapse;width:100%;margin-top:10px;}")
        f.write(".pass{background:#d4edda;} .fail{background:#f8d7da;}")
        f.write(".summary{margin-bottom:20px;} .toggle{cursor:pointer;color:blue;text-decoration:underline;}")
        f.write("</style>")
        f.write("<script>")
        f.write("function toggle(id){var e=document.getElementById(id);e.style.display=(e.style.display=='none')?'block':'none';}")
        f.write("</script>")
        f.write("</head><body>")

        f.write("<h1>Test Results Report</h1>")
        f.write(f"<p><b>Generated:</b> {timestamp}</p>")
        f.write("<div class='summary'>")
        f.write(f"<p><b>Total:</b> {total} &nbsp; <b>Pass:</b> {passed} &nbsp; <b>Fail:</b> {failed} &nbsp; <b>Iterations:</b> {iterations}</p>")
        f.write("</div>")

        f.write("<table>")
        f.write("<tr><th>iteration</th><th>command_name</th><th>command</th><th>expected</th><th>regex</th>"
                "<th>negative</th><th>wait_till</th><th>print_after</th><th>print_ahead_chars</th>"
                "<th>message</th><th>retries</th><th>found</th><th>result</th></tr>")

        for i, r in enumerate(results, 1):
            result = r.get("result", "")
            css = "pass" if result == "PASS" else "fail"
            snippet_id = f"snippet{i}"
            found = r.get("found", "")

            f.write(f"<tr class='{css}'>")
            f.write(f"<td>{r.get('iteration','')}</td>")
            f.write(f"<td>{r.get('command_name','')}</td>")
            f.write(f"<td>{r.get('command','')}</td>")
            f.write(f"<td>{r.get('expected','')}</td>")
            f.write(f"<td>{r.get('regex','')}</td>")
            f.write(f"<td>{r.get('negative','')}</td>")
            f.write(f"<td>{r.get('wait_till','')}</td>")
            f.write(f"<td>{r.get('print_after','')}</td>")
            f.write(f"<td>{r.get('print_ahead_chars','')}</td>")
            f.write(f"<td>{r.get('message','')}</td>")
            f.write(f"<td>{r.get('retries','')}</td>")
            f.write(f"<td><span class='toggle' onclick=\"toggle('{snippet_id}')\">View</span>"
                    f"<div id='{snippet_id}' style='display:none;white-space:pre-wrap;border:1px solid #ccc;"
                    f"margin-top:4px;padding:4px;'>{found.replace('<','&lt;').replace('>','&gt;')}</div></td>")
            f.write(f"<td>{result}</td>")
            f.write("</tr>")

        f.write("</table></body></html>")

    try:
        webbrowser.open(filename)
    except Exception:
        pass
