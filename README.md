# Engineering Guardian — Codex 软件工程与自审 Skill

> A reusable, evidence-driven engineering skill for Codex: design → implement → verify → review → improve.
>
> 用《代码大全2》软件构建原则建立可执行工程闭环，支持安全的自动巡检与受控迭代。

## 功能 / Capabilities

- **需求与架构 / Design first**：明确范围、接口、非功能指标和变化边界，按风险选择设计深度。
- **质量构建 / High-quality construction**：单一职责、信息隐藏、明确类型与命名、边界处理、适度抽象。
- **自动自审 / Self-review**：两遍审查（正确性/安全性、可维护性/变更风险），基于证据输出分级发现。
- **可执行门禁 / Quality gates**：本地零依赖审计器、Skill 结构校验、单测、CI 验证。
- **持续更新 / Controlled evolution**：每周检查白名单官方规范的变化，自动创建草稿 PR；可选 Codex Agent 生成规则改进草稿，必须经人工审阅才能合并。

**重要边界：** 自动脚本 ≠ 形式化正确性证明，也不等于模型已经“永久学会”。未经测试的代码不能宣称已验证；任何规则更新不会自动合并到 `main`。

## 安装 / Install

1. 克隆本仓库，或下载 ZIP 并解压。
2. 将 `skills/engineering-guardian` 整个目录复制到目标项目的 `.agents/skills/engineering-guardian/`（项目级），或 `~/.agents/skills/engineering-guardian/`（个人级）。
3. 在 Codex 新会话中输入：`Use $engineering-guardian to implement/review this change.`
4. 如希望 Codex 在仓库工作时始终遵守基本规则，可将根目录 `AGENTS.md` 复制到你的项目根目录，然后按项目补充测试命令。

> 对已有项目，**不要无条件覆盖原有 AGENTS.md**；请合并且保持已有项目指令的优先级和安全约束。

## 本地检查 / Local verification

```bash
python3 skills/engineering-guardian/scripts/validate_skill.py
python3 -m unittest discover -s tests -v
python3 skills/engineering-guardian/scripts/check_repo.py --root . --format text
python3 tools/refresh_sources.py --check
```

检查其他项目：

```bash
python3 skills/engineering-guardian/scripts/check_repo.py --root /path/to/project --format json
python3 skills/engineering-guardian/scripts/review_diff.py --repo /path/to/project --base origin/main
```

发现 `HIGH/BLOCKER` 应人工复核并修复。扫描是启发式的，可能有误报和漏报，**不得把“零发现”作为安全证明**。

## 项目结构 / Layout

```text
skills/engineering-guardian/
  SKILL.md                      Codex 触发与执行流程
  agents/openai.yaml            Skill 界面信息
  references/engineering.md     软件工程核心原则与依据
  references/review.md          审查报告标准与严重度
  references/technology.md      语言/项目类型适配
  references/evolution.md       自我改进、证据与审批策略
  scripts/validate_skill.py     Skill 结构校验
  scripts/check_repo.py         零依赖静态风险巡检
  scripts/review_diff.py        Git diff 风险评估
.github/workflows/
  ci.yml                        每次 PR 自动自检
  standards-watch.yml           每周来源变化检测与 PR
  codex-improvement.yml         可选 Codex 修订草稿 PR
.github/dependabot.yml          GitHub Actions 依赖更新提案
maintenance/                    受信任的来源清单与更新记录
```

## 自动更新 / Auto maintenance

- **无密钥可用**：每周 GitHub Actions 检查官方页面变化，变更时创建草稿 PR，**不改变核心规范**；更新 GitHub Actions 依赖也由 Dependabot 提 PR。
- **可选 AI 改进**：在 GitHub 仓库 Secret 中设置 `OPENAI_API_KEY`，手动运行 `Codex Improvement Proposal` 工作流，自动检查已观察的证据、撰写改进建议；只有能核实权威变化时才允许对 `references/technology.md` 提出受限规则修改，并提交草稿 PR。启用前请检查组织的 GitHub Actions 权限和 API 费用。
- **批准标准**：存在明确的权威来源或真实缺陷、无冲突、通过全部测试、至少一次独立审查、人工合并。
- **没有授权自动合并**。AI 只允许改动提案文档与指定的技术适配参考文件；未经人工合并不会影响正式版本。所有更新保留 commit/PR 记录以便回滚。

## 适配范围

兼容 Python、TypeScript/JavaScript、Web/微信小程序等项目的通用工程工作流；具体测试、编译、格式化、安全检查应由项目 `AGENTS.md` 提供实际命令。未提供命令时，Skill 不能假装已运行。

## 来源与版权 / Attribution

理论源于 Steve McConnell 的 *Code Complete, 2nd Edition*（2004）及其公开配套 Checklists，也参考了 OpenAI Codex Skills 与 GitHub Actions 相关公开文档。**本仓库未包含原书或用户上传的 PDF 正文**，规则为独立归纳并结合现代工程实践编写。

- Code Complete: https://www.microsoftpressstore.com/store/code-complete-9780735691254
- Supplementary checklists (copyright Steven C. McConnell, conditional non-commercial re-use): https://www.matthewjmiller.net/files/cc2e_checklists.pdf
- OpenAI Skills: https://developers.openai.com/api/docs/guides/tools-skills
- GitHub Actions security: https://docs.github.com/en/actions/reference/security/secure-use

本仓库原创内容遵循 [MIT License](LICENSE)。Checklists 的特殊授权**不等于原书进入公有领域**；此仓库不转载其完整内容。

## 状态 / Status

v0.1.0 — 初版工程规范与静态测试已实现；GitHub 工作流需在真实仓库发布后触发验证。运行 Codex AI 提案需要另行设置 API Key。持续效果需通过实际项目的缺陷率、回归测试结果与维护成本验证。

## 发布到 GitHub / Publishing

建议新建公开仓库 `codex-engineering-guardian`，不要将独立 Skill 混入现有业务项目。创建空仓库后，在本目录执行：

```bash
git init -b main
git add .
git commit -m "feat: initial Engineering Guardian Skill"
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/codex-engineering-guardian.git
git push -u origin main
```

如果本机安装并登录了 GitHub CLI，也可直接执行 `gh repo create codex-engineering-guardian --public --source=. --remote=origin --push`。选择公开/私有仓库取决于你的实际发布意图；公开前再次扫描是否存在企业或私人资料。GitHub Actions 如需自行创建草稿 PR，需要仓库允许 Actions 创建 Pull Request，且仓库/组织策略允许工作流所请求的写权限。**首次发布后先手动触发 CI 与 Standards Watch 验证配置，不应把未运行的云端流程描述为已验证。**
