"""政务信息公开申请审查系统 —— 命令行入口。

用法示例：
  # 交互式输入申请
  python main.py --interactive

  # 从文件读取申请
  python main.py --input samples/申请示例.txt

  # 指定判例目录与输出文件
  python main.py -i samples/申请示例.txt -p precedents -o 报告.html

  # 调用大模型润色建议（需先设置 LLM_API_KEY 等环境变量）
  python main.py -i samples/申请示例.txt --llm
"""
import argparse
import sys
import datetime
from config import Config
from advisor import run_analysis
from report import build_report


def _read_text_robust(path: str) -> str:
    """兼容多种常见编码（UTF-8 / UTF-8-BOM / GBK / UTF-16）读取文本。"""
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "gbk", "utf-16"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="ignore")


def _read_input(args):
    if args.interactive:
        print("请输入市民提交的政务信息公开申请内容（单独一行输入 END 结束）：")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip() == "END":
                break
            lines.append(line)
        return "\n".join(lines)
    if args.input:
        return _read_text_robust(args.input)
    return None


def main():
    parser = argparse.ArgumentParser(description="政务信息公开申请合规审查与判例比对工具")
    parser.add_argument("--input", "-i", help="市民申请文本文件路径（.txt/.md）")
    parser.add_argument("--output", "-o", help="输出 HTML 报告路径")
    parser.add_argument("--precedents", "-p", default="precedents", help="判例语料目录（默认 precedents）")
    parser.add_argument("--interactive", action="store_true", help="交互式输入申请内容")
    parser.add_argument("--llm", action="store_true", help="调用大模型润色建议（需配置 LLM_API_KEY 等环境变量）")
    args = parser.parse_args()

    text = _read_input(args)
    if not text or not text.strip():
        print("请提供 --input 文件 或 使用 --interactive。详见 python main.py --help")
        sys.exit(1)

    cfg = Config.from_env(precedents_dir=args.precedents)
    result, precedents, advisory = run_analysis(text, cfg.precedents_dir, use_llm=args.llm)

    date = datetime.date.today().isoformat()
    out = args.output or f"审查报告_{date}.html"
    html = build_report(text, result, precedents, advisory, date)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print("=" * 56)
    print(f"合规评分：{result.score}")
    print(f"处理建议：{result.recommendation}")
    for it in result.issues:
        print(f"  [{'/'.join([it['level']])}] {it['point']} （依据：{it['basis']}）")
    print(f"匹配判例：{len(precedents)} 条")
    for p in precedents[:3]:
        d = p["doc"]
        print(f"  - {d.get('title','')}  相关度 {p['score']}")
    print(f"报告已生成：{out}")


if __name__ == "__main__":
    main()
