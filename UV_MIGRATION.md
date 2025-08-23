# UV迁移指南

## 🚀 已完成的迁移

我们已将后端项目从pip迁移到uv，享受更快的包管理和现代化的开发体验。

### 迁移内容

1. **新增配置文件**
   - `pyproject.toml` - 项目依赖和配置
   - `.python-version` - Python版本固定为3.9
   - `UV_MIGRATION.md` - 本迁移说明

2. **更新配置**
   - `vercel.json` - 更新为使用main.py（FastAPI）而不是index.py

3. **保留文件**
   - `requirements.txt` - 保持兼容性，Vercel仍可使用
   - `main.py` - FastAPI实现（推荐）
   - `index.py` - 原生HTTP实现（备用）

## 📦 如何使用uv

### 安装uv
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 项目开发命令

**安装依赖**
```bash
# 进入backend-stub目录
cd backend-stub

# 安装项目依赖
uv sync

# 或安装到当前环境
uv pip install -e .
```

**开发环境**
```bash
# 安装开发依赖
uv sync --dev

# 运行服务器
uv run uvicorn main:app --reload --port 8000
```

**添加新依赖**
```bash
# 添加生产依赖
uv add requests
uv add openai

# 添加开发依赖  
uv add --dev pytest
```

**代码质量工具**
```bash
# 格式化代码
uv run black .
uv run isort .

# 代码检查
uv run ruff .

# 运行测试
uv run pytest
```

## 🔄 回滚方案

如果需要回滚到pip：

1. 删除uv相关文件：
   ```bash
   rm pyproject.toml .python-version UV_MIGRATION.md
   ```

2. 恢复vercel.json中的index.py配置

3. 继续使用requirements.txt

## 🎯 推荐工作流

1. **日常开发**
   ```bash
   cd backend-stub
   uv sync              # 同步依赖
   uv run uvicorn main:app --reload
   ```

2. **添加AI依赖时**
   ```bash
   uv add httpx         # HTTP客户端
   uv add openai        # OpenAI SDK
   uv add anthropic     # Claude SDK
   ```

3. **部署前检查**
   ```bash
   uv run ruff .        # 代码检查
   uv run black .       # 格式化
   ```

## 📝 注意事项

- **Vercel兼容性**: Vercel会自动识别pyproject.toml或requirements.txt
- **Python版本**: 固定为3.9确保一致性
- **依赖锁定**: uv会自动生成uv.lock确保依赖版本一致
- **向后兼容**: requirements.txt保留，确保现有工作流正常

## 🚀 uv的优势体现

迁移完成后，你将体验到：
- **10-100倍更快的依赖安装**
- **更好的依赖解析和冲突检测**  
- **统一的项目配置管理**
- **现代化的开发工具链**

现在可以安全地使用uv进行开发，同时保持与现有工作流的兼容性！