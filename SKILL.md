---
name: china-legal-cold-start
description: Builds a China-law legal practice profile by interviewing the user about role, jurisdictions, practice modules, document templates, research sources, risk preferences, and output style. Use when setting up China-law legal agent skills, starting a new matter, configuring contract review, dispute resolution, compliance, labor, corporate, investment, IP, data compliance, or legal research workflows.
---

# China Legal Cold Start

## Purpose

Use this skill to build a reusable China-law legal practice profile before other legal skills start drafting, reviewing, researching, or managing matters.

The goal is not to ask every possible question. The goal is to learn:

- who the user is and what level of legal judgment they can exercise;
- which China-law practice modules are actually active;
- what jurisdictions, regulators, courts, arbitral institutions, and research sources matter;
- what templates, review standards, risk levels, and house style the user already uses;
- what matter-specific context should override the general profile.

Do not treat China law as one uniform workflow. Mainland China, Hong Kong, Macau, Taiwan, and cross-border matters require different assumptions. Mainland China work may also vary by local court, regulator, industry, and transaction type.

## Core Rules

1. Ask only for active modules. Do not collect litigation details from a contract-only user or IPO details from a labor-only user.
2. Prefer documents over memory. When a question likely has an existing source, ask for a file path, pasted text, or short summary before asking the user to retype it.
3. Never silently fill legal facts. If a statute, deadline, regulator, filing threshold, jurisdiction, case name, or license type is uncertain, mark it as `[需核验]` and ask before writing it into the profile.
4. Distinguish legal work product from legal advice. If the user is not a licensed lawyer or is outside attorney supervision, frame outputs as research notes, draft materials, and issues for lawyer review.
5. Preserve the user's house style. Extract structure, risk labels, citation style, and drafting conventions from seed documents whenever possible.
6. Keep placeholders deliberate. Before writing the profile, list missing answers and ask whether to fill them now or leave them as `[待补充]`.

## Cold-Start Check

Look for an existing profile at `.cursor/legal-profiles/china-legal-profile.md` in the current workspace.

- If it does not exist, start the interview.
- If it contains `<!-- SETUP PAUSED AT: -->`, offer to resume from that section or restart.
- If it exists and has no pause marker, confirm whether the user wants to update it, redo it, or create a matter-specific profile.

For personal cross-project use, ask whether the user wants a profile under `~/.cursor/legal-profiles/china-legal-profile.md` instead. Do not move or overwrite an existing profile without confirmation.

## Opening Preamble

Say this before the first question:

> 我会先建立一个中国法工作画像：你是谁、做哪些法律模块、适用哪些法域、常用哪些模板、风险口径是什么。这样后续合同审查、诉讼文书、合规分析或法律检索不会从通用模板开始，而是按你的团队习惯输出。
>
> 可以快速设置，也可以完整设置。快速设置约 2 分钟，只记录身份、法域、模块和默认输出格式；完整设置会读取你的模板或过往文档，提取风险等级、审查阈值、引用格式和文书风格。
>
> 你想走“快速”还是“完整”？

Wait for the user's choice before continuing.

## Interview Pacing

- Ask no more than 2-3 answerable prompts in one turn.
- For uploaded or pasted documents, read them first, extract what can be extracted, then confirm with the user.
- For long answers, say: `这个问题需要你输入或提供文件，我等你。`
- If the user says pause, stop, or later, write a partial profile with a pause marker and `[待补充]` fields.

## Part 0: User Role and Supervision

Ask:

> 你日常会以什么身份使用这个 skill？
>
> 1. 执业律师 / 实习律师 / 律师助理
> 2. 公司法务 / 合规 / 法务运营
> 3. 法学院学生 / 研究人员
> 4. 业务人员、创始人、HR、采购、销售等非法务角色
> 5. 其他，请简单说明

Then ask:

> 是否有执业律师、合伙人、总法律顾问、法务负责人或外部律师对你的工作进行复核？

If the user is not a lawyer or has no regular legal supervision, record:

- outputs should be framed as research notes or draft materials;
- legal-consequence actions require a lawyer-review reminder;
- the agent should prepare a concise attorney-review brief when needed.

Write this to `## User role and supervision`.

## Part 1: Jurisdiction and Legal Sources

Ask:

> 你的工作主要涉及哪些法域？可以多选或自由描述：大陆中国、中国香港、中国澳门、中国台湾、跨境交易、境外上市、涉外争议、其他。

Ask:

> 你通常需要引用或核验哪些来源？例如法律法规、司法解释、部门规章、地方规定、监管问答、交易所规则、裁判文书、指导案例、公报案例、类案检索、公司内部制度、行业规范。

For Mainland China work, record whether the user needs:

- current-effective law checks;
- local rules or local court views;
- regulator-specific views, such as SAMR, CAC, CSRC, PBOC, SAFE, MOHRSS, tax authorities, stock exchanges, or industry regulators;
- citation format with article numbers and effective dates.

Write this to `## Jurisdiction and legal sources`.

## Part 2: Module Selection

Ask:

> 哪些是你的常规工作模块？可以多选。
>
> 1. 合同审查与起草
> 2. 公司治理与工商事项
> 3. 投融资、并购、股权交易
> 4. 争议解决：诉讼、仲裁、执行、保全
> 5. 劳动用工
> 6. 合规与监管
> 7. 数据合规与个人信息保护
> 8. 知识产权与商业秘密
> 9. 法律研究、类案检索、法律备忘录
> 10. 其他

Record active modules on an `**Active modules:**` line. Only run the module interviews that apply.

## Part 3C: Contract Module

Use if contract review or drafting is active.

Ask for seed documents first:

> 你有没有常用合同模板、合同审查清单、红线版示例、风险评级表或过往审查意见？可以提供文件路径、粘贴内容，或说“暂无”。我会先从文档里提取审查口径，避免让你重新输入。

Extract:

- contract types;
- review position: buyer-friendly, seller-friendly, balanced, internal risk-control;
- risk labels, such as high / medium / low, red / yellow / green, must-change / negotiable / note-only;
- key clauses: subject matter, payment, delivery, acceptance, IP, confidentiality, data, compliance, liability, termination, dispute resolution;
- fallback language and non-negotiable positions;
- output format: checklist, table, memo, redline comments, email summary.

If no seed document is provided, ask:

- Which contract types are most common?
- What issues must always be escalated?
- What output format should be the default?

Write to `## Contract review and drafting`.

## Part 3G: Corporate and Investment Module

Use if company governance, investment, M&A, or equity work is active.

Ask for seed documents first:

> 有无章程、股东协议、董事会/股东会决议、股权转让协议、增资协议、投资协议、尽调清单、披露清单或交割清单模板？可以提供路径、粘贴内容，或说“暂无”。

Extract:

- company type: limited liability company, company limited by shares, partnership, foreign-invested enterprise, VIE or offshore structure;
- decision-making bodies and approval thresholds;
- common transaction types;
- signing and closing process;
- diligence categories;
- disclosure schedule or issue memo format;
- approval and escalation rules.

Ask only if not extractable:

- What entity or transaction types do you usually handle?
- What approvals or filings often matter?
- Who signs off on material issues?

Write to `## Corporate, governance, and investment`.

## Part 3D: Dispute Resolution Module

Use if litigation, arbitration, enforcement, preservation, or demand letters are active.

Ask for seed documents first:

> 有无起诉状、答辩状、代理词、证据目录、法律意见、律师函、庭审提纲、保全申请或类案检索报告模板？可以提供路径、粘贴内容，或说“暂无”。

Extract:

- forum: court, arbitration commission, enforcement court, mediation center;
- matter types;
- pleading style and structure;
- evidence list format;
- claim calculation format;
- citation and case-reference style;
- local court or arbitral institution preferences;
- review and filing workflow.

Ask only if needed:

- Which dispute types are common?
- Which courts, regions, or arbitral institutions appear most often?
- Should outputs be client-facing, court-facing, or internal analysis?

Write to `## Dispute resolution`.

## Part 3L: Labor Module

Use if labor and employment work is active.

Ask for seed documents first:

> 有无员工手册、劳动合同、竞业限制协议、解除通知、协商解除协议、绩效改进计划、劳动仲裁文书或用工合规清单？可以提供路径、粘贴内容，或说“暂无”。

Extract:

- employee types and locations;
- common issues: hiring, termination, transfer, salary adjustment, discipline, non-compete, social insurance, overtime, dispatch, contractor classification;
- approval and escalation standards;
- document templates;
- HR-facing versus legal-facing output style.

Ask only if needed:

- Which cities or provinces matter most?
- Which actions require legal review before HR proceeds?
- What level of business-friendly practicality should outputs use?

Write to `## Labor and employment`.

## Part 3R: Compliance, Data, IP, and Research

Use this section for any selected compliance, data, IP, or research module.

Ask:

> 这些模块中，你最常处理哪些具体事项？例如广告合规、反不正当竞争、反垄断、反商业贿赂、出口管制、数据出境、个人信息保护、网络安全、商标、著作权、专利、商业秘密、开源合规、法律研究或类案检索。

Ask for seed documents:

> 有无合规制度、评估表、DPIA/个人信息保护影响评估、隐私政策、数据处理协议、投诉处理记录、知识产权清单、检索报告或法律备忘录模板？

Extract:

- applicable regulators and laws;
- risk rating method;
- approval or filing triggers;
- citation requirements;
- business-facing output format;
- whether the user requires source verification before conclusions.

Write to the relevant sections:

- `## Compliance and regulation`
- `## Data and personal information`
- `## Intellectual property`
- `## Legal research`

## Matter-Specific Setup

When the user starts a specific contract, case, transaction, compliance project, or research task, create or update `.cursor/legal-profiles/matters/[matter-code].md`.

Ask only matter-specific questions:

- matter code or short name;
- parties;
- jurisdiction or forum;
- matter type;
- key documents or folder path;
- deadlines;
- risk tolerance;
- responsible reviewer or approver;
- any deviations from the general profile.

Matter-specific context overrides the general profile only for that matter.

## Profile Output Template

Write the profile in this structure:

```markdown
# China Legal Practice Profile

**Active modules:** [modules]
**Last updated:** [date]

## User role and supervision
[role, supervision model, output framing]

## Jurisdiction and legal sources
[法域、监管机关、检索来源、引用要求、核验要求]

## Output style
[语言、格式、风险等级、引用格式、是否客户可直接阅读]

## Contract review and drafting
[only if active]

## Corporate, governance, and investment
[only if active]

## Dispute resolution
[only if active]

## Labor and employment
[only if active]

## Compliance and regulation
[only if active]

## Data and personal information
[only if active]

## Intellectual property
[only if active]

## Legal research
[only if active]

## Open items
- [待补充] ...
```

## Quality Check Before Writing

Before writing or updating the profile, summarize:

- active modules;
- documents received and what was extracted;
- legal facts requiring verification;
- skipped fields that will be marked `[待补充]`;
- any assumptions that may affect future outputs.

Ask:

> 我准备把这些内容写入你的中国法工作画像。还有哪些现在要补充？如果没有，我会把空缺项明确标成 `[待补充]`，不会假装已经知道。

Wait for confirmation.

## After Writing

Tell the user:

> 已写入中国法工作画像。之后合同审查、诉讼文书、合规分析、类案检索或投融资文件处理都会优先读取这个画像。你可以随时说“更新我的中国法画像：……”来修改某个偏好、阈值、模板或模块。

Then suggest the most relevant next action based on active modules, for example:

- contract active: review one real contract using the profile;
- dispute active: build a case timeline and evidence checklist;
- corporate active: analyze a transaction document set or governance approval path;
- compliance active: run a compliance issue-spotting memo;
- research active: create a legal research memo with source-verification requirements.

## Failure Modes

- Do not translate US legal concepts into China-law terms without checking fit.
- Do not assume attorney-client privilege rules from US practice apply.
- Do not cite law, cases, or regulatory guidance as current unless verified.
- Do not ask for irrelevant seed documents from inactive modules.
- Do not write vague thresholds like "material contracts" without asking what "material" means in RMB, contract type, business importance, or risk category.
- Do not merge Mainland China, Hong Kong, Macau, and Taiwan into one undifferentiated legal analysis.
