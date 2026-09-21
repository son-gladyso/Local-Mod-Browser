# Local MOD Browser

一个面向本地 MOD 资料的 Windows 浏览器与协作平台。它把用户自己持有的目录元数据
整理成可搜索的 Nexus 风格界面，并让网页、CLI 和可选 MCP 适配器共享同一套本地 API。

> English summary: a privacy-first, local-only MOD catalog browser and workflow
> platform for Windows. It indexes metadata supplied by the user; it does not
> download, redistribute, install, or execute MOD files.

## 特性

- 搜索、组合标签、分页、详情、图片、收藏、具体文件比较与搭配导入导出。
- 资料修订、翻译任务、可恢复批处理、任务租约和五条确定性 AI 工作流。
- HTTP、CLI、MCP 共用契约 `2.5.0`，共 70 项操作。
- SQLite WAL/FULL、配对备份、恢复日志、幂等回执和公平写入调度。
- 核心服务只使用 Python 标准库，只监听 `127.0.0.1`。

## 支持范围

- Windows 10/11 x64。
- 首次安装固定运行时需要联网，并需要一个可用的系统 Python 来执行引导脚本。
- 项目固定运行时为 CPython 3.13.15 x64 与 SQLite 3.53.4；来源和校验值见
  [`runtime-lock.json`](runtime-lock.json)。
- Linux 和 macOS 当前不受支持。

## 快速开始

```powershell
git clone <your-fork-or-repository-url> Local-Mod-Browser
cd Local-Mod-Browser
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

示例配置会读取仓库中的虚构演示目录。打开启动命令输出的本机 URL，即可在不提供
私人 MOD 库的情况下查看空库/演示流程。也可以双击 `启动MOD浏览器.cmd`。

配置自己的目录时，编辑被 Git 忽略的 `data/sources.json`：

```json
[
  {
    "key": "mygame",
    "title": "My Game",
    "root": "D:\\Mods\\My Game",
    "outputDir": "D:\\Mods\\My Game\\catalog"
  }
]
```

每个 `outputDir` 中放置 `catalog-data.json`。相对路径以 `sources.json` 所在目录
为基准；也可通过 `LOCAL_MOD_BROWSER_SOURCES` 指向另一份配置。格式示例见
[`examples/demo-game/catalog-data.json`](examples/demo-game/catalog-data.json)。

## CLI

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

详细说明见 [`docs/user-guide.md`](docs/user-guide.md)、
[`docs/ai-platform-guide.md`](docs/ai-platform-guide.md) 和
[`docs/architecture.md`](docs/architecture.md)。

## 验证

```powershell
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v
.\.runtime\python.exe -X utf8 tests\startup_acceptance.py
.\.runtime\python.exe -X utf8 tests\collaboration_acceptance.py
python -m pip install jsonschema==4.26.0
python -X utf8 tests\contract_audit.py --fixture
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
```

浏览器验收另需 `npm install` 和 Playwright 浏览器；详见贡献指南。CI 默认运行不依赖
真实库存的合成回归、契约审计和 JavaScript 语法检查。

## 隐私、内容与第三方服务

- 仓库不包含 MOD、图片、作者正文、个人库存、数据库、备份、导出或运行令牌。
- `data/`、`exports/`、`backups/`、`test-results/` 和 `.runtime/` 默认不进入 Git。
- 本项目不附带 Nexus 数据抓取器或库存快照；使用第三方服务时请遵守其条款。
- 本项目不安装或运行 MOD，也不保证 MOD 的兼容性、安全性或来源真实性。

## 许可证

项目代码使用 [MIT License](LICENSE)。第三方运行时和可选依赖的说明见
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。MIT 许可不授予任何 MOD、
游戏素材、站点数据或其他第三方内容的权利。
