
## 快速开始

### 环境要求

- Python 3.10+（推荐 3.11）
- Windows / macOS / Linux 均可；浏览器自动化依赖 Chromium（由 Playwright 安装）

### 安装

```bash
cd sanctions-screening   # 或克隆后的项目根目录
pip install -r requirements.txt
python -m playwright install chromium
```

### 配置密钥（切勿提交 `.env`）

```bash
copy .env.example .env   # Windows；Unix 使用 cp
```

编辑 `.env`，填入：

- `OPENSANCTIONS_API_KEY` — [OpenSanctions API](https://www.opensanctions.org/api/)
- `TAVILY_API_KEYS` 或 `TAVILY_API_KEY` — [Tavily](https://tavily.com/)

本仓库 **`.gitignore` 已排除 `.env`**；若您曾将密钥写入其他文件并误提交，请立即**轮换密钥**并自 Git 历史中清除敏感提交（可使用 `git filter-repo` 等工具，或新建空仓库仅保留净提交）。

### 命令行示例（从项目根目录执行）

初筛与情报汇总（阶段 1 思路，具体参数见 `SKILL.md`）：

```bash
python scripts/screen_entity.py "Example Corp" --type LegalEntity -o Example_api_report.md
```

官网核验与 HTML/PDF 报告（阶段 2+，需已安装 Playwright）：

```bash
python scripts/browser_verify.py "Example" --type Entity --extra-variants "example corp" -o screenshots/ --report Example_sanctions_report.html --api-report Example_api_report.md
```

批量场景见 `scripts/batch_screen.py`。

---

## 目录结构（核心文件）

| 路径 | 用途 |
|------|------|
| `SKILL.md` | AI/自动化执行规范与完整阶段说明（**必读**） |
| `references/legal_implications.md` | 各清单法律影响叙述模板（撰写报告时引用） |
| `references/false_positive_check.md` | 误中判断指引 |
| `references/us_lists_coverage.md` | 美国主要清单覆盖说明 |
| `references/red_flags_checklist.md` | BIS「了解你的客户」类红旗检查参考 |
| `scripts/screen_entity.py` | 初筛 + 情报 + 校验计划整合 |
| `scripts/browser_verify.py` | 官网自动化检索与截图、报告生成 |
| `scripts/opensanctions_search.py` / `tavily_search.py` | API 封装 |
| `requirements.txt` | Python 依赖一览 |

**仓库范围：** 仅同步 `SKILL.md`、`references/`、`scripts/` 及上述配置文件。运行产生的 `screenshots/`、`*_sanctions_report.*`、`*_api_report.md` 以及微信推广类文稿等已列入 `.gitignore`，留在本地即可，不会进入 Git。

---

## 风险评级与报告解读

工具使用多维度评分输出风险等级（如 CRITICAL / HIGH / MEDIUM 等），区间与建议动作见 `SKILL.md`「报告解读」一节。使用时建议：

- 将**评级**视为**排程与复核优先级**的参考，而非替代《出口管理条例》《国际紧急经济权力法》等规则下的实体分析；
- 对**疑似误中**条目必须人工复核全名、地址、别名与主体类型；
- 在对外交付中明确**筛查时间、检索式、数据源版本与限制条件**。