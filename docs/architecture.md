# 项目地图

本文描述公开版 2.5.0/70 操作契约的模块边界。公开仓只包含合成示例；自动化、
故障、性能、迁移与恢复测试必须使用 `test-results` 下的隔离副本。

## AI 工作平台 v2

`contracts.py` 是操作名称、参数、结果、示例及读写性质的唯一来源；HTTP `/api/v2`、生成的 CLI 命令和可选 MCP 适配器共用此定义。`platform_api.py` 复用既有业务函数，业务修改与 operation_receipts 在同一事务内提交。`catalog.atomic` 让旧函数借用外层连接，禁止内层提前提交。

`work_runtime.py` 使用同目录的 work-runtime.sqlite3 保存任务、租约、作业、事件和运行回执；单写作业队列、并行读取。工作任务与作业分开；启动通过业务回执恢复真实状态。`interchange.py` 维护来源导入、批次快照、变更序号和资料问题报告。迁移采用事务并在首次 v2 迁移前备份。

运行库的 `job_batches` 保存分批边界、输入哈希、操作版本、资源版本、状态和逐批进度；业务库保存不可变执行计划、批次边界和权威回执。分批模式先完成整包预览，再按最多 50 条资源记录／译文分段或 512 KiB 提交；译文完整字段在所有分段齐全、质检和版本复核后原子发布。重启时业务回执优先于运行库进度，已提交批次直接跳过。`write_scheduler.py` 让旧 API、v2 和后台作业共用可重入写门，前后台分别 FIFO、按 4∶1 调度；后台队首等待两秒后可提前一次，但两类都排队时不会连续执行后台批次。

`observability.py` 在内存中按操作和阶段聚合单调时钟耗时，提供 P50/P95/P99、样本量与关联 ID；诊断快照最多每分钟写入 `diagnostics/metrics.jsonl`，不保存参数、正文、凭据或路径。`maintenance.metrics` 读取指定时间窗口的摘要。

`platform_client.py` 是 CLI 与 MCP 的标准库客户端：发现本机服务、核对契约主版本、短暂错误最多退避三次，并在写响应丢失后先查业务回执。`TaskSession` 自动续租，在到期前安全窗口停止新增写入；等待外部翻译时保存检查点并释放租约。`workflows.json` 是五条流程的机器定义，`workflows.py` 只解析其中登记的操作和参数引用，每次恢复只执行一步。

完整工作流和准确限制见 `ai-platform-guide.md`。核心无额外依赖；MCP 与浏览器验收
使用单独的可选依赖。

## 数据流

`data/sources.json` → 用户提供的 `catalog-data.json` → catalog.rebuild → SQLite 目录索引 → server HTTP API → 中文网页与 ai.py。

人或 AI 的资料修改 → content.preview_edits → content.apply_preview → edits + edit_history + 当前目录。重建先写 resource_base，再套用 edits；收藏、搭配、翻译不清空。数据库使用 WAL；重建在单事务发布，取消保留上一次索引。离线来源保留旧索引。

公开仓不携带站点抓取器或个人库存快照。任何外部元数据必须由用户在本地、在有权
使用的前提下提供，并通过同一预览/提交链进入数据库。

## 模块边界

| 模块 | 职责 / 修改入口 |
|---|---|
| catalog.py | 标准化来源、资源 ID、索引、路径重定位、译文状态；事务维护查询摘要、有效译文和标签投影 |
| content.py | 可编辑字段白名单、乐观版本校验、预览提交、历史、搭配导入 |
| translations.py | 分段、保护标识、任务包、分段导入和全文完成校验 |
| server.py | 本机 HTTP、安全边界、查询分页、收藏搭配、后台任务、API_DOC |
| launcher.py | 启动锁、探活、复用服务、后台启动 |
| ai.py | JSON CLI，自动处理会话令牌、错误退出码、文件交换和任务等待 |
| static/app.js | 浏览、详情、具体副本、比较、收藏、搭配、画廊、翻译 |
| static/editor.js | 人用资料编辑、搭配导入、批量资料导入导出 |
| static/style.css | 深色响应式布局；800 / 1250 / 1700 px 断点 |
| tests/ | 临时数据库回归和独立服务浏览器验收 |
| observability.py | 隐私安全的关联 ID、分阶段延迟聚合与诊断快照 |
| write_scheduler.py | 前台／后台公平写入门和最长等待保护 |
| platform_client.py | HTTP/CLI/MCP 共用重试、回执核对与任务租约会话 |
| workflows.json / workflows.py | 五条白名单业务流程、运行检查点和外部等待 |
| lifecycle_lock.py / restore_platform.py | 服务全生命周期目录锁、配对备份、SQLite 恢复日志与中断恢复 |
| runtime_support.py / tools/bootstrap_runtime.py | 选择、安装并验证固定 Python/SQLite 运行时 |

运行不需要 Node；Node + Playwright 只用于浏览器测试。避免引入打包步骤或隐藏代码生成，让下一位 AI 可以直接读文件定位功能。

## 持久数据与身份

- MOD：`game:ModId`。本地无编号内容：`game:local:hash`，哈希基于相对路径集合。
- 文件：`game:ModId:file:FileId`；无法证实 FileId 的归档为 `local-hash`。同 FileId 的多个路径合并 copies，选择记录每个 fileId 只存一份副本。
- 本地无编号身份依赖相对路径；直接改名或改变路径集合会产生新 ID。迁移整盘请用根目录映射，不直接改身份。
- games/mods/files/images/resource_base 是目录；favorites/recent/settings/profiles/selections 是个人数据；edits/edit_history 是覆盖；translations/translation_history/translation_tasks 是翻译；previews 是短期校验结果。
- schemaVersion=1 的搭配清单是中立交换格式；尚无 GMM 适配。
- 正式业务库是 `data/catalog.sqlite3`，同目录的 `work-runtime.sqlite3` 保存任务、
  作业与运行状态。可供配对恢复的备份由 `maintenance.backup` 生成两库及
  `manifest.json`；旧 `/api/backup` 只备份业务库。Git 只回退代码，不回退用户数据。

## API 约定

成功 `{ok:true,data:...}`，失败 `{ok:false,error:{code,message}}`。GET 查询，POST 修改；鉴权来自本机 session。只监听 127.0.0.1，校验 Host / Origin / X-Mod-Token；图片只从登记目录索引读，下载限 exports。请求体最大 32 MiB。

`/api/docs` 描述全部路线；`/api/schema` 提供 JSON Schema。页面每页 48，接口上限 96；画廊每批 24。列表、翻译状态、组合标签、总数和分面在同一 SQLite 读取快照中使用 SQL 投影计算，只解码当前页；原文、译文、任务或算法版本变化时投影在业务事务内更新或失效，过期译文不会继续显示为完成。

## 修改后的验证

```powershell
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
git diff --check
```

上述命令是提交前基本回归。浏览器测试见 `tests/browser.cjs`；专用数据库和 runtime
用于避免触碰用户数据。运行产物放入 `test-results`（Git 忽略）。
