# 编剧系统多智能体架构 - 正式启用指南

> 版本: 1.0
> 状态: 已激活
> 启用日期: 2026-03-29

---

## 一、系统概览

### 1.1 双赛道架构

```
┌─────────────────────────────────────────────────────────────┐
│                    创作系统 Creation System                    │
├─────────────────────────┬───────────────────────────────────┤
│   短视频赛道 (short)     │   网文长篇赛道 (long)              │
│   3-5分钟剧本创作         │   100万字+小说创作                 │
├─────────────────────────┼───────────────────────────────────┤
│ • Hook生成               │ • 世界观架构                        │
│ • 冲突密度设计            │ • 角色成长线                        │
│ • 情绪曲线规划            │ • 主线/支线编织                     │
│ • 结尾Punchline          │ • 断章设计                          │
│ • 平台合规检测            │ • 防崩检测                          │
└─────────────────────────┴───────────────────────────────────┘
```

### 1.2 五大铁律风控

| 铁律 | 级别 | 说明 |
|------|------|------|
| IR-001 价值观安全 | 阻断 | 禁止敏感内容 |
| IR-002 版权合规 | 阻断 | 禁止抄袭洗稿 |
| IR-003 平台规则 | 警告 | 符合平台规范 |
| IR-004 逻辑自洽 | 警告 | 剧情前后一致 |
| IR-005 人设稳定 | 阻断 | 角色不OOC |

### 1.3 核心工作流

```
Day1: 需求确认 → step1-diag → 赛道选择
Day2: 人设/世界观 → step2-blueprint → 系统蓝图
Day3: 剧情/结构 → step3-strategy → 策略路径
Day4: 工业化组件 → step4-resource → 资源配置
Day5: 拉片分析 → story-analyzer → 标准化分析
Day6: 迭代优化 → iteration-engine → 差距改进
Day7: 测试启用 → step7-review → 验收复盘
```

---

## 二、快速开始

### 2.1 创建第一个项目

```bash
# 短视频剧本
python -m cli.main script-short create "逆袭打工人" --platform douyin --genre 励志

# 网文长篇
python -m cli.main script-long create "修真狂徒" --platform qidian --genre 玄幻 --words 100
```

### 2.2 使用工业化组件

```bash
# 查看可用组件
python -m cli.main component list

# 加载组件到项目
python -m cli.main component load char-001
```

### 2.3 拉片分析

```bash
# 分析作品
python -m cli.main analyze story {project_id}

# 生成改进方案
python -m cli.main analyze iterate {project_id}

# 生成个人报告
python -m cli.main report personal
```

---

## 三、命令参考

### 3.1 短剧本命令 (script-short)

| 命令 | 功能 |
|------|------|
| create | 创建新项目 |
| outline | 生成大纲 |
| draft | 生成草稿 |
| list | 列出项目 |

### 3.2 网文命令 (script-long)

| 命令 | 功能 |
|------|------|
| create | 创建新项目 |
| world | 设计世界观 |
| character | 创建角色 |
| volumes | 规划分卷 |

### 3.3 分析命令 (analyze)

| 命令 | 功能 |
|------|------|
| story | 拉片分析 |
| iterate | 迭代优化 |
| compare | 对标分析 |

### 3.4 报告命令 (report)

| 命令 | 功能 |
|------|------|
| personal | 个人创作报告 |
| export | 沉淀到知识库 |

---

## 四、目录结构

```
AI-Platform/
├── creation/                 # 创作系统
│   ├── short/               # 短视频赛道
│   │   ├── projects/        # 项目文件夹
│   │   └── templates/       # 剧本模板
│   ├── long/                # 网文赛道
│   │   ├── projects/
│   │   ├── worldbuilding/   # 世界观库
│   │   └── characters/      # 人设库
│   ├── components/          # 工业化组件库
│   │   ├── characters/      # 人设组件
│   │   ├── scenes/          # 桥段组件
│   │   └── payoffs/         # 爽点组件
│   └── analysis/            # 拉片报告
│       ├── templates/       # 分析模板
│       └── reports/         # 报告存档
├── core/                    # 核心引擎
│   ├── creation_agents.py   # 创作Agent
│   ├── story_analyzer.py    # 拉片分析
│   ├── iteration_engine.py  # 迭代优化
│   ├── component_engine.py  # 组件引擎
│   ├── script_guard.py      # 五大铁律
│   └── creation_bridge.py   # 数据沉淀
└── cli/                     # 命令接口
    ├── creation_commands.py # 创作命令
    └── analysis_commands.py # 分析命令
```

---

## 五、人机协同规范

### 5.1 AI风控（不可修改）

- **价值观安全**: 触碰即阻断，必须整改
- **版权合规**: 检测到风险即阻断
- **人设稳定**: 检测到OOC即阻断

### 5.2 人工决策点

| 决策 | 人工 | AI |
|------|------|-----|
| 赛道选择 | ✓ 必须 | 建议 |
| Hook选择 | ✓ 必须 | 生成选项 |
| 创意方向 | ✓ 必须 | 生成选项 |
| 组件选择 | ✓ 按需 | 推荐 |
| 迭代确认 | ✓ 必须 | 生成方案 |

### 5.3 数据沉淀规则

- 每次创作完成 → 自动沉淀到知识库
- 每次拉片分析 → 生成可复习笔记
- 每次迭代优化 → 记录改进路径
- 每周生成 → 个人创作报告

---

## 六、系统禁忌

1. **禁止跨赛道混合**: short与long完全隔离
2. **禁止跳过风控**: 所有产出必须通过ScriptGuard
3. **禁止绕过确认**: 关键决策点必须人工确认
4. **禁止超限加载**: 同类型组件最多3个
5. **禁止忽略沉淀**: 每次创作必须数据沉淀

---

## 七、支持与反馈

- 系统文档: `steps/step7/编剧系统多智能体架构优化方案.md`
- 测试脚本: `tests/test_creation_system.py`
- 启用指南: `ACTIVATION_GUIDE.md` (本文档)

---

**系统已正式启用，祝创作顺利！**
