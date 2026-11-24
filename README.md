# agent-from-scratch

从零手写 LLM Agent 的五阶段渐进式 Python 教学代码库（无 LangChain 等重框架依赖，已归档于 `archive/from-home/agent-from-scratch`）。

## 阶段结构

- `01_chat.py`：裸调 Chat Completions HTTP API（含 429 指数退避重试）
- `02_tool_use.py`：工具声明（Function Calling）与本地函数分发
- `03_react.py`：ReAct（Reasoning + Acting）多步推理与观察闭环
- `04_memory.py`：基于 `memory.json` 的会话与长期记忆持久化
- `05_action.py` / `05_streaming.py`：受控沙箱执行（`sandbox/`）与流式输出

## 目标平台（Target 判定）

- **移动端**：可选（CLI 教学脚本）
- **智能硬件**：可选（可搁置）

## 快速运行与验证

```bash
# 配置模型 API Key 后运行任意阶段脚本
export ZHIPU_API_KEY="your-key"
python3 01_chat.py

# 运行归档冒烟测试
npm test
```

## 归档说明

家用机迁入归档工程；活跃演进版见 `active/agent-from-scratch`。
