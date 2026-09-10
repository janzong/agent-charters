"""agent-charters —— 人写给 AI 智能体的书面规约（AGENTS.md）的结构化语料库。

用法:
    from agent_charters import load_corpus, analyze_file

    corpus = load_corpus()
    mine = analyze_file("AGENTS.md")
    print(mine["categories"])
"""

from .extract import (analyze_file, analyze_text, category_coverage,
                      load_corpus, substantive)
from .taxonomy import CATEGORIES, RULESET_VERSION, VERSION

__version__ = "0.2.0"

__all__ = [
    "CATEGORIES",
    "RULESET_VERSION",
    "VERSION",
    "analyze_file",
    "analyze_text",
    "category_coverage",
    "load_corpus",
    "substantive",
]
