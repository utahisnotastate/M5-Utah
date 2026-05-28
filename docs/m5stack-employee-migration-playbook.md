# M5Stack Employee Migration Playbook / M5Stack 员工迁移手册

## Executive message / 执行摘要

**EN**  
This project is designed to make the current repository sprawl *operationally obsolete* for new development by consolidating behavior into one stable runtime surface.  
Existing repositories do not disappear overnight, but their role shifts from “active primary implementation” to “compatibility reference and archival baseline.”

**中文**  
本项目旨在通过统一运行时界面，使当前仓库分散模式在新开发中“运维层面过时”。  
现有仓库不会一夜消失，但角色会从“主实现仓库”转为“兼容参考与归档基线”。

---

## 1) Why migrate now / 为什么现在迁移

**EN**
- Faster iteration: host-side logic updates in seconds.
- Lower maintenance: fewer duplicated protocol implementations.
- Better onboarding: one architecture to teach.
- Better quality: shared runtime primitives and reusable tests.
- Better product velocity: coordinated feature rollout across hardware lines.

**中文**
- 迭代更快：主机逻辑可秒级更新。
- 维护成本更低：减少重复协议实现。
- 培训更简单：统一架构易于上手。
- 质量更稳定：共享运行时原语与可复用测试。
- 产品速度更高：跨硬件线统一推进功能。

---

## 2) Organizational impact map / 组织影响图

**EN**
- Firmware teams: maintain thin, reliable terminal runtime.
- SDK teams: implement intent APIs and typed client tooling.
- Solutions teams: build use-case flows in host scripts/services.
- QA teams: test protocol and behavior contracts, not fragmented libraries.
- Developer relations: teach one model, publish one migration path.
- Sales engineering: demo faster with configurable intent workflows.

**中文**
- 固件团队：维护轻量、可靠的终端运行时。
- SDK 团队：构建意图 API 与类型化客户端工具。
- 解决方案团队：在主机脚本/服务中构建场景流程。
- QA 团队：验证协议与行为契约，而非碎片化库。
- 开发者关系团队：教授统一模型，发布统一迁移路径。
- 售前工程团队：通过可配置意图流程快速演示。

---

## 3) Repository obsolescence strategy / 仓库“过时化”策略

**EN**
Define clear states for existing repositories:
1. **Retire**: no active usage, superseded by registry + intent.
2. **Reference**: keep for historical context and edge compatibility.
3. **Bridge**: temporary wrappers forwarding to unified runtime.
4. **Core**: the new active consolidation repository (this one).

Policy:
- No new feature work in retired/reference repos.
- Critical fixes only during transition window.
- All new functionality lands in unified runtime paths.

**中文**
为现有仓库定义清晰状态：
1. **退役**：不再活跃使用，已由注册表 + 意图替代。
2. **参考**：用于历史上下文与边缘兼容。
3. **桥接**：过渡期包装层，转发到统一运行时。
4. **核心**：新的活跃整合仓库（本仓库）。

策略：
- 退役/参考仓库禁止新增功能开发。
- 迁移窗口期仅允许关键修复。
- 所有新功能统一落在整合运行时路径。

---

## 4) 30-60-90 day migration plan / 30-60-90 天迁移计划

### Days 0-30: Foundation / 0-30 天：基础建设

**EN**
- Freeze net-new API expansion in fragmented repos.
- Establish migration office hours and owners.
- Build unit inventory and capability matrix.
- Define compatibility SLA and deprecation policy.
- Deliver 3 golden-path demos on unified substrate.

**中文**
- 冻结分散仓库新增 API 扩展。
- 建立迁移答疑机制与负责人体系。
- 建立 Unit 清单与能力矩阵。
- 制定兼容 SLA 与弃用策略。
- 在统一底座上交付 3 条黄金路径演示。

### Days 31-60: Port and validate / 31-60 天：迁移与验证

**EN**
- Port top 20 customer workflows.
- Implement bridge adapters for high-traffic legacy APIs.
- Create integration and regression suites.
- Publish internal migration cookbook by role.

**中文**
- 迁移前 20 个高频客户工作流。
- 为高流量旧 API 实现桥接适配器。
- 建立集成与回归测试套件。
- 按角色发布内部迁移手册。

### Days 61-90: Enforce and sunset / 61-90 天：收敛与退场

**EN**
- Enforce “new features only in unified runtime” policy.
- Announce retirement timeline for low-value legacy repos.
- Track and publish migration KPIs weekly.
- Move teams from exception mode to standard operating mode.

**中文**
- 强制执行“新功能只进统一运行时”策略。
- 公布低价值旧仓库退役时间表。
- 每周跟踪并发布迁移 KPI。
- 团队从例外状态切换到标准作业状态。

---

## 5) Role-based tutorials / 按岗位教程

## A) Firmware engineer tutorial / 固件工程师教程

**EN**
Goal: keep firmware stable, minimal, deterministic.

Steps:
1. Build and flash `firmware/`.
2. Confirm telemetry and ACK framing.
3. Add only generic hardware intent handlers.
4. Reject feature requests that belong in host policy.
5. Add tests for protocol backward compatibility.

Completion criteria:
- no business rules in MCU loop
- bounded loop timing
- all public JSON contracts documented

**中文**
目标：保持固件稳定、最小、确定性。

步骤：
1. 编译并烧录 `firmware/`。
2. 验证遥测与 ACK 帧格式。
3. 只增加通用硬件意图处理器。
4. 将应属主机策略层的需求拒绝下放到固件。
5. 补齐协议向后兼容测试。

完成标准：
- MCU 循环中无业务规则
- 循环时延有上界
- 所有公开 JSON 契约有文档

## B) Python/SDK engineer tutorial / Python 与 SDK 工程师教程

**EN**
Goal: implement composable intent APIs and wire graph primitives.

Steps:
1. Install package from `host/`.
2. Build typed wrappers over raw JSON intents.
3. Create reusable FluxGraph templates.
4. Add schema validation and robust error typing.
5. Ship CLI and SDK examples for core customer scenarios.

Completion criteria:
- stable API signatures
- clear exception model
- examples runnable in under 5 minutes

**中文**
目标：实现可组合意图 API 与 Wire 图原语。

步骤：
1. 从 `host/` 安装包。
2. 在原始 JSON 意图之上构建类型化封装。
3. 创建可复用 FluxGraph 模板。
4. 增加模式校验与健壮错误类型。
5. 交付覆盖核心客户场景的 CLI/SDK 示例。

完成标准：
- API 签名稳定
- 异常模型清晰
- 示例 5 分钟内可跑通

## C) QA engineer tutorial / QA 工程师教程

**EN**
Goal: validate contract compatibility and behavioral correctness.

Steps:
1. Build a test matrix by board and capability.
2. Create replay tests from captured telemetry logs.
3. Verify ACK semantics for valid and invalid intents.
4. Run long-duration soak tests on serial reliability.
5. Track defect classes eliminated by consolidation.

Completion criteria:
- protocol compliance suite green
- regression suite for top use cases
- reliability reports published

**中文**
目标：验证契约兼容性与行为正确性。

步骤：
1. 按板卡与能力建立测试矩阵。
2. 基于遥测日志构建回放测试。
3. 验证合法/非法意图的 ACK 语义。
4. 执行串口可靠性长稳测试。
5. 统计整合后被消除的缺陷类型。

完成标准：
- 协议一致性测试通过
- 核心场景回归套件完整
- 可靠性报告定期发布

## D) Product manager tutorial / 产品经理教程

**EN**
Goal: reduce roadmap friction and accelerate cross-device delivery.

Steps:
1. Prioritize features as intent capabilities, not per-repo tasks.
2. Require migration impact notes in every new feature spec.
3. Track KPI: lead time, defect escape rate, onboarding time.
4. Sunset low-value legacy commitments with communication plans.
5. Align release notes to unified architecture milestones.

Completion criteria:
- roadmap framed around unified substrate
- measurable migration KPI improvement

**中文**
目标：降低路线图摩擦，加速跨设备交付。

步骤：
1. 以意图能力而非“按仓库任务”来规划功能。
2. 每个新功能规格必须包含迁移影响说明。
3. 跟踪 KPI：交付周期、缺陷逃逸率、上手时长。
4. 通过沟通计划逐步下线低价值历史承诺。
5. 发布说明按统一架构里程碑组织。

完成标准：
- 路线图围绕统一底座展开
- 迁移 KPI 可量化改善

## E) Developer relations tutorial / 开发者关系教程

**EN**
Goal: teach one mental model to community and partners.

Steps:
1. Replace per-unit tutorials with intent-centric tutorials.
2. Provide “legacy to unified” migration examples.
3. Standardize demo scripts based on host runtime.
4. Publish bilingual docs and starter templates.
5. Collect external friction and feed into registry/API backlog.

Completion criteria:
- doc consistency across channels
- reduced support tickets for “which repo/library”

**中文**
目标：向社区与合作伙伴传达统一心智模型。

步骤：
1. 用“意图中心教程”替代“按 Unit 教程”。
2. 提供“旧方案到统一方案”迁移示例。
3. 统一基于主机运行时的演示脚本。
4. 发布中英双语文档与模板。
5. 收集外部阻力并进入注册表/API 待办。

完成标准：
- 各渠道文档一致
- “该用哪个仓库/库”的支持单显著下降

---

## 6) Training program by employee type / 员工类型培训计划

**EN**
- **New hire (technical):** 2-day bootcamp, architecture + hands-on lab.
- **New hire (non-technical):** 2-hour overview, workflow and vocabulary.
- **Support/Sales:** script-first demos, troubleshooting checklist.
- **Manufacturing/Test Ops:** firmware consistency, fixture automation hooks.
- **Leadership:** KPI dashboard and governance cadence.

**中文**
- **技术新员工：** 2 天训练营，架构 + 实操实验。
- **非技术新员工：** 2 小时概览，流程与术语培训。
- **支持/售前：** 脚本化演示与排障清单。
- **生产/测试运营：** 固件一致性与治具自动化接口。
- **管理层：** KPI 看板与治理节奏。

---

## 7) KPI framework / KPI 框架

**EN**
Track weekly:
- % of new features shipped in unified runtime
- # legacy repos receiving net-new code
- mean time to first successful prototype
- bug escape rate by product line
- onboarding time to first contribution

Targets (example):
- 90%+ new features on unified runtime by day 90
- 70% reduction in active legacy repositories by day 180

**中文**
按周追踪：
- 新功能落在统一运行时的占比
- 仍在新增代码的旧仓库数量
- 首个可运行原型平均时间
- 各产品线缺陷逃逸率
- 新人首个贡献上手时间

示例目标：
- 第 90 天前，90%+ 新功能在统一运行时交付
- 第 180 天前，活跃旧仓库减少 70%

---

## 8) Communication templates / 沟通模板

### A) Internal announcement / 内部公告

**EN**
“Starting today, new M5Stack feature development defaults to the unified Resolver Substrate. Legacy repositories move into compatibility mode. Teams should use the migration playbook and office hours for transition support.”

**中文**
“即日起，M5Stack 新功能开发默认采用统一 Resolver Substrate。旧仓库进入兼容模式。各团队请使用迁移手册与答疑机制完成过渡。”

### B) Legacy deprecation notice / 旧仓库弃用通知

**EN**
“This repository is now in maintenance mode. New features are implemented in the unified runtime repository. Critical fixes remain supported until the posted sunset date.”

**中文**
“本仓库现已进入维护模式。新功能请在统一运行时仓库实现。公布的退场日期前仍支持关键修复。”

---

## 9) Migration risks and mitigations / 迁移风险与缓解

**EN**
- Risk: team inertia -> Mitigation: clear owners, strict policy gates.
- Risk: compatibility regressions -> Mitigation: bridge adapters + regression suites.
- Risk: unclear boundaries -> Mitigation: architecture decision records.
- Risk: documentation drift -> Mitigation: bilingual docs with versioned review cadence.

**中文**
- 风险：团队惯性 -> 缓解：明确负责人 + 强制策略门禁。
- 风险：兼容回归 -> 缓解：桥接适配器 + 回归测试。
- 风险：边界不清 -> 缓解：架构决策记录（ADR）。
- 风险：文档漂移 -> 缓解：中英双语文档 + 版本化评审节奏。

---

## 10) Immediate next actions / 今日立即行动

**EN**
1. Adopt this repository as the default for net-new feature work.
2. Assign one migration owner per department.
3. Classify top 50 legacy repositories by retire/reference/bridge/core.
4. Schedule weekly migration KPI review.
5. Publish this playbook internally in both English and Chinese.

**中文**
1. 将本仓库设为新增功能默认入口。
2. 各部门指定 1 位迁移负责人。
3. 对前 50 个旧仓库完成退役/参考/桥接/核心分类。
4. 建立每周迁移 KPI 评审。
5. 以内网形式发布本中英双语手册。
