"""申请合规性规则检查器。

基于《政府信息公开条例》对市民提交申请做结构化初筛，输出：
  - 合规评分（0-100）
  - 问题清单（级别 / 要点 / 法条依据 / 处置建议）
  - 命中的不予公开情形类别
  - 总体处理建议
"""
import re
from regulations import NON_DISCLOSURE_KEYWORDS, ABUSE_KEYWORDS


class ComplianceResult:
    def __init__(self):
        self.issues = []            # [{level, point, basis, suggestion}]
        self.flags = {}             # category -> bool
        self.score = 100
        self.detected_categories = []   # 命中的不予公开类别
        self.extracted = {}         # 抽取到的字段状态
        self.recommendation = ""

    def add_issue(self, level, point, basis, suggestion, deduction=0):
        self.issues.append({
            "level": level, "point": point,
            "basis": basis, "suggestion": suggestion,
        })
        self.score = max(0, self.score - deduction)


class ComplianceChecker:
    def analyze(self, text: str) -> ComplianceResult:
        res = ComplianceResult()
        t = text or ""

        # 1) 申请人身份信息
        has_name = bool(re.search(r'(申请人|姓名|名称|单位|公司)[\s:：]*[一-龥A-Za-z0-9]{2,}', t)) or "本人" in t
        has_contact = bool(re.search(r'(1[3-9]\d{9}|[\w.]+@[\w.]+|[一-龥]{2,}(省|市|区|县|路|号|街|村))', t)) or ("联系方式" in t) or ("电话" in t)
        res.extracted["has_name"] = has_name
        res.extracted["has_contact"] = has_contact
        if not has_name:
            res.add_issue("补正", "缺少申请人姓名 / 名称等身份信息", "条例第29条第1项",
                          "一次性告知申请人补正身份信息", deduction=25)
        if not has_contact:
            res.add_issue("补正", "缺少有效联系方式", "条例第29条第1项",
                          "一次性告知申请人补正联系方式", deduction=15)

        # 2) 申请内容明确性
        has_intent = bool(re.search(r'(申请(公开|获取)|公开以下|请求公开|查阅|复制)', t))
        plain_len = len(re.sub(r'\s', '', t))
        has_content = has_intent and plain_len >= 20
        res.extracted["has_content"] = has_content
        if not has_content:
            res.add_issue("补正", "申请公开的政府信息描述不明确（缺少名称/文号/特征性描述）",
                          "条例第29条第2项、第30条",
                          "一次性告知申请人在合理期限内补正（一般不超过15个工作日），逾期视为放弃", deduction=25)

        # 3) 不予公开情形初筛
        for cat, kws in NON_DISCLOSURE_KEYWORDS.items():
            if any(kw in t for kw in kws):
                res.detected_categories.append(cat)
        if res.detected_categories:
            res.add_issue("审查", "申请内容可能触及法定不予公开情形：" + "、".join(res.detected_categories),
                          "条例第14-16条、第36条第3项",
                          "逐条审查是否确属法定不予公开范围；涉及第三方权益的应先书面征求意见（第32条），并区分可公开与不予公开部分", deduction=10)

        # 4) 滥用申请初筛
        abuse_hit = [kw for kw in ABUSE_KEYWORDS if kw in t]
        if abuse_hit:
            res.add_issue("审查", "申请数量/频次可能明显超过合理范围：" + "、".join(abuse_hit),
                          "条例第35条、第42条",
                          "可要求申请人说明理由；理由不合理的告知不予处理；理由合理但无法按期答复的可确定延迟答复期限", deduction=5)

        res.recommendation = self._recommend(res)
        return res

    @staticmethod
    def _recommend(res: ComplianceResult) -> str:
        has_fix = any(i["level"] == "补正" for i in res.issues)
        if has_fix:
            return ("建议：作出补正告知 —— 自收到申请之日起7个工作日内一次性告知申请人在合理期限"
                    "（一般≤15个工作日）内补正；申请人无正当理由逾期不补正的，视为放弃申请，行政机关不再处理"
                    "（条例第30条）。")
        if res.detected_categories:
            return ("建议：进入不予公开情形审查 —— 逐条核对法定不予公开范围（条例第14-16条）；如涉及第三方合法"
                    "权益，应书面征求第三方意见（第32条）；确不予公开的，书面告知并说明理由（第36条第3项）。"
                    "须在20个工作日内答复（可延长≤20个工作日）。")
        if any(i["level"] == "审查" for i in res.issues):
            return ("建议：结合审查要点依法处理，注意答复期限（条例第33条）与可能的信息处理费（第42条）。")
        return ("建议：予以公开 —— 自收到申请之日起20个工作日内予以答复（可延长≤20个工作日），"
                "并告知获取方式、途径和时间（条例第33条、第36条第2项）。")
