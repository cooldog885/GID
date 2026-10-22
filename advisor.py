"""建议生成器：整合合规性检查与判例比对结果，产出处理建议。

默认采用规则化生成（离线可用）；当配置了 LLM_API_KEY 等环境变量且 use_llm=True 时，
可调用兼容 OpenAI 接口的大模型进一步润色建议（需在可信内网环境使用）。
"""
import json
import urllib.request
from config import Config
from compliance import ComplianceChecker
from precedent_search import load_corpus, search


def run_analysis(application_text: str, precedents_dir: str = "precedents", use_llm: bool = False):
    checker = ComplianceChecker()
    result = checker.analyze(application_text)
    docs = load_corpus(precedents_dir)
    precedents = search(docs, application_text, top_k=5)
    advisory = generate_advisory(result, precedents, use_llm=use_llm)
    return result, precedents, advisory


def generate_advisory(result, precedents, use_llm: bool = False):
    lines = []
    lines.append(result.recommendation)
    if result.detected_categories:
        lines.append("需重点审查的不予公开类别：" + "、".join(result.detected_categories) + "。")
    if precedents:
        lines.append("参考判例：")
        for p in precedents[:3]:
            d = p["doc"]
            lines.append(f"  · {d.get('title','')}（{d.get('court','')} {d.get('doc_id','')}）"
                         f"—— 裁判要旨：{d.get('outcome','')}（相关度 {p['score']}）")
    else:
        lines.append("未匹配到本地判例语料，建议补充 wenshu.court.gov.cn 中相关文书后重新比对。")

    advisory = "\n".join(lines)

    if use_llm:
        try:
            advisory = _llm_enhance(advisory)
        except Exception as e:
            print(f"[warn] 大模型建议生成失败，已回退规则建议：{e}")
    return advisory


def _llm_enhance(base_advisory: str) -> str:
    import os
    api_key = os.getenv("LLM_API_KEY", "")
    api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    if not api_key:
        return base_advisory
    prompt = (
        "你是政务信息公开审查辅助助手。下面是一份市民申请的合规初筛结论与参考判例，"
        "请据此给出简洁、可操作的处理建议（中文，不超过300字），并明确提示最终须由经办人员依法决定：\n\n"
        + base_advisory
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        api_base.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()
