# GitHub Code Analyzer

一个用于分析GitHub仓库核心代码实现的Claude Skill，帮助产品经理理解代码库的技术架构和核心逻辑。

## 功能

- 接收GitHub仓库链接
- 自动分析项目结构、技术栈、核心模块
- 深入分析关键代码实现
- 生成产品经理易懂的Markdown报告

## 使用方式

在Claude Code/Cursor中，直接发送GitHub链接即可：

```
帮我分析 https://github.com/facebook/react
```

## 分析报告内容

- 项目概览（名称、语言、功能描述）
- 技术架构（技术栈、框架、依赖）
- 核心模块分析（关键类/函数、代码解读）
- 数据流程（流程图、接口、存储）
- 核心业务逻辑（业务流程、关键代码位置）
- 总结（技术特点、业务价值、适用场景）

## 安装

将 skill 放置到 `~/.claude/skills/` 目录下。
