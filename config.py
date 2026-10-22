"""配置模块：所有敏感凭证均从环境变量读取，绝不硬编码到代码中。

使用前请在 shell / 运行环境中设置：
    set WENSHU_USERNAME=13918378355
    set WENSHU_PASSWORD=******        （请勿写入任何文件）
    set LLM_API_KEY=******            （可选，调用大模型生成建议时使用）
    set LLM_API_BASE=https://your-api-endpoint
    set LLM_MODEL=your-model-name
"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    wenshu_username: str = ""
    wenshu_password: str = ""
    llm_api_key: str = ""
    llm_api_base: str = ""
    llm_model: str = "default"
    precedents_dir: str = "precedents"

    @classmethod
    def from_env(cls, precedents_dir: str = "precedents") -> "Config":
        return cls(
            wenshu_username=os.getenv("WENSHU_USERNAME", ""),
            wenshu_password=os.getenv("WENSHU_PASSWORD", ""),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_api_base=os.getenv("LLM_API_BASE", ""),
            llm_model=os.getenv("LLM_MODEL", "default"),
            precedents_dir=precedents_dir,
        )
