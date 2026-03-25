# AutoCode Marketplace

AutoCode 插件的 Claude Code Marketplace 分发仓库。

## 安装方式

### 1. 添加 Marketplace

```bash
/plugin marketplace add git@gitlab.allcam.com.cn:dev-flow/autocode-marketplace.git
```

### 2. 安装插件

```bash
/plugin install autocode@autocode-marketplace
```

### 3. 更新插件

```bash
/plugin marketplace update
```

## 包含的插件

### autocode

AI 研发全流程工作流插件，包含：

- **7 个智能体** — 需求分析师、架构设计师、开发计划师、特性开发者、测试工程师、文档评审员、模块分析师
- **7 个工作流命令** — `/ac:analysis-rq`、`/ac:develop-rq`、`/ac:prepare-rq`、`/ac:init-project`、`/ac:fix-bug`、`/ac:analyze-modules`、`/ac:check-env`
- **38 个技能包** — 覆盖需求分析、架构设计、缺陷修复、环境检查、远程调试等场景

## 维护说明

本仓库由 `build-marketplace.sh` 脚本自动构建，源码位于 [ai-flow-rad](https://gitlab.allcam.com.cn/dev-flow/ai-flow-rad) 仓库的 `autocode/` 目录。
