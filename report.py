"""HTML 报告生成（自包含，CSS 内联，可直接浏览器打开）。"""

DISCLAIMER = (
    "本工具输出仅为辅助性合规参考，<b>不构成正式行政决定</b>。"
    "最终答复须由经办人员依据《中华人民共和国政府信息公开条例》及本单位内部规程依法作出。"
    "判例比对基于本地语料，不构成穷尽检索，亦不作为司法裁判依据。"
)


def _escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _score_color(score: int) -> str:
    if score >= 80:
        return "#2e7d32"
    if score >= 60:
        return "#f9a825"
    return "#c62828"


def build_report(application_text, result, precedents, advisory, date):
    score = result.score
    color = _score_color(score)

    # 问题清单
    issues_html = ""
    if result.issues:
        rows = "".join(
            f"<tr><td><span class='lv lv-{_escape(i['level'])}'>{_escape(i['level'])}</span></td>"
            f"<td>{_escape(i['point'])}</td>"
            f"<td class='basis'>{_escape(i['basis'])}</td>"
            f"<td>{_escape(i['suggestion'])}</td></tr>"
            for i in result.issues
        )
        issues_html = f"""
        <h2>一、合规检查问题清单</h2>
        <table>
          <thead><tr><th>级别</th><th>要点</th><th>法条依据</th><th>处置建议</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>"""
    else:
        issues_html = "<h2>一、合规检查问题清单</h2><p class='ok'>未发现明显合规缺陷。</p>"

    # 判例
    prec_html = ""
    if precedents:
        rows = "".join(
            f"<tr><td>{_escape(p['doc'].get('title',''))}</td>"
            f"<td>{_escape(p['doc'].get('court',''))} {_escape(p['doc'].get('doc_id',''))}</td>"
            f"<td>{_escape(p['doc'].get('outcome',''))}</td>"
            f"<td class='score'>{p['score']}</td>"
            f"<td class='tags'>{_escape('、'.join(p['doc'].get('tags', []) or []))}</td></tr>"
            for p in precedents
        )
        prec_html = f"""
        <h2>二、参考判例比对（来自本地语料）</h2>
        <table>
          <thead><tr><th>案件</th><th>法院/案号</th><th>裁判要旨</th><th>相关度</th><th>标签</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>"""
    else:
        prec_html = "<h2>二、参考判例比对</h2><p class='warn'>未匹配到本地判例语料，请补充 precedents/ 目录后重试。</p>"

    cats = "、".join(result.detected_categories) or "无"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>政务信息公开申请审查报告</title>
<style>
  body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;margin:0;background:#f4f6f8;color:#222}}
  .wrap{{max-width:960px;margin:0 auto;padding:24px}}
  header{{background:#1f3a5f;color:#fff;padding:20px 24px;border-radius:10px}}
  header h1{{margin:0;font-size:20px}}
  header .meta{{font-size:13px;opacity:.85;margin-top:6px}}
  .card{{background:#fff;border-radius:10px;padding:18px 22px;margin:16px 0;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
  .summary{{display:flex;align-items:center;gap:24px}}
  .gauge{{font-size:42px;font-weight:700}}
  .rec{{flex:1;font-size:15px;line-height:1.6}}
  h2{{font-size:16px;border-left:4px solid #1f3a5f;padding-left:10px;margin:8px 0 14px}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  th,td{{border:1px solid #e3e7ec;padding:8px 10px;text-align:left;vertical-align:top}}
  th{{background:#eef2f6}}
  .lv{{display:inline-block;padding:1px 8px;border-radius:10px;color:#fff;font-size:12px}}
  .lv-补正{{background:#f9a825}} .lv-审查{{background:#1565c0}} .lv-提示{{background:#757575}}
  .basis{{color:#555}}
  .score{{font-weight:700;color:#1565c0;text-align:center}}
  .tags{{color:#777}}
  .ok{{color:#2e7d32}} .warn{{color:#c62828}}
  .advisory{{background:#fff8e1;border-left:4px solid #f9a825;padding:12px 16px;border-radius:6px;white-space:pre-wrap;line-height:1.7}}
  pre.app{{background:#f0f3f6;padding:12px;border-radius:6px;white-space:pre-wrap;font-size:13px;max-height:240px;overflow:auto}}
  .disc{{font-size:12px;color:#666;margin-top:18px;line-height:1.6}}
</style></head>
<body><div class="wrap">
<header>
  <h1>政务信息公开申请审查报告</h1>
  <div class="meta">生成日期：{_escape(date)} ｜ 合规评分（仅供参考）</div>
</header>

<div class="card summary">
  <div class="gauge" style="color:{color}">{score}</div>
  <div class="rec"><b>处理建议：</b><br>{_escape(result.recommendation)}<br>
  <span style="font-size:13px;color:#666">命中不予公开情形：{_escape(cats)}</span></div>
</div>

<div class="card">
  <h2>市民原始申请</h2>
  <pre class="app">{_escape(application_text)}</pre>
</div>

<div class="card">{issues_html}</div>

<div class="card">{prec_html}</div>

<div class="card">
  <h2>三、综合处理建议</h2>
  <div class="advisory">{_escape(advisory)}</div>
</div>

<div class="disc">免责声明：{DISCLAIMER}</div>
</div></body></html>"""
    return html
