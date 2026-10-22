"""本地判例语料加载与相似度比对。

语料目录（默认 precedents/）支持：
  - *.json ：{"title","court","date","doc_id","tags":[],"outcome","content"}
  - *.txt  ：纯文本裁判文书，文件名作为标题
将中国裁判文书网（wenshu.court.gov.cn）中"政府信息公开"相关文书手动导出后放入该目录即可参与比对。

匹配策略：以 LEGAL_TERMS 法律术语重合度为主，标签重合为辅，给出相关度评分并排序。
"""
import os
import re
import json
import glob
from regulations import LEGAL_TERMS


def load_corpus(directory: str):
    docs = []
    if not os.path.isdir(directory):
        return docs
    for path in sorted(glob.glob(os.path.join(directory, "**", "*"), recursive=True)):
        if os.path.isdir(path):
            continue
        try:
            if path.endswith(".json"):
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                d["_path"] = path
                docs.append(d)
            elif path.endswith(".txt"):
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                docs.append({
                    "title": os.path.splitext(os.path.basename(path))[0],
                    "court": "", "date": "", "doc_id": "",
                    "tags": [], "content": content, "_path": path,
                })
        except Exception as e:
            print(f"[warn] 无法加载语料文件 {path}: {e}")
    return docs


def extract_terms(text, term_list=LEGAL_TERMS):
    t = text or ""
    return set(term for term in term_list if term in t)


def _bigrams(text):
    s = re.sub(r"\s+", "", text or "")
    return set(s[i:i + 2] for i in range(len(s) - 1))


def search(docs, query: str, top_k: int = 5):
    q_terms = extract_terms(query)
    q_bg = _bigrams(query)
    results = []
    for d in docs:
        content = (d.get("content", "") or "") + " " + (d.get("title", "") or "")
        d_terms = extract_terms(content)
        shared = q_terms & d_terms
        score = len(shared) * 2                      # 法律术语重合（主信号）
        shared_bg = q_bg & _bigrams(content)
        score += min(len(shared_bg), 50) * 0.2       # 字符二元组重合（语义兜底）
        for tag in (d.get("tags") or []):
            if tag in query:
                score += 5
        if score > 0:
            results.append({"doc": d, "score": round(score, 1),
                            "shared": list(shared)})
    results.sort(key=lambda x: -x["score"])
    return results[:top_k]
