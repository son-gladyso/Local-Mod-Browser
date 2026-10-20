# Local MOD Browser

[简体中文](../../README.md) · [English](../../README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md) · [Русский](README.ru.md) · [繁體中文](README.zh-TW.md)

這些語言選項翻譯的是 README，不代表應用介面或所有連結指南已經多語言化。

**版本狀態（2026-10-20）：** 下一版正在獨立驗收，尚未發布。當前公開版本仍為 `v2.5.2`（API 契約 `2.5.0`）；下文安裝步驟、功能和安全邊界均針對當前公開版。開發候選及使用者本地截圖中的新功能，不應視為已隨公開版提供。

<p align="center"><img src="../assets/logo-small.png" alt="Local MOD Browser logo" width="112"></p>

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![Contract](https://img.shields.io/badge/API%20contract-2.5.0-6f42c1)
[![CI](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml/badge.svg)](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml)

> **你的 MOD 庫，不該只是幾個越來越大的資料夾。**
>
> 用一個本地、可搜尋、可恢復、能與 AI 協作的資料工作臺，把“我記得有這個 MOD”變成
> “我能在幾秒內找到它、核對它、繼續處理它”。
>
> **下載過一些 MOD，卻忘了當初為什麼下載、它們各自有什麼功能？** 已有的摘要、功能說明與標籤能幫你找回上下文；也可以手動把今後的使用計畫寫進搭配備註。瀏覽器不會自動推斷你當初的下載動機。

[立即開始](#五分钟开始使用) · [下載 v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2) · [檢視 AI 介面](#cli-与-ai-协作) · [瞭解安全邊界](#安全边界与隐私设计) · [提交建議](https://github.com/son-gladyso/Local-Mod-Browser/issues)

<a id="把散落在硬盘里的-mod变成真正可用的个人资料库"></a>

## 把散落在硬碟裡的 MOD，變成真正可用的個人資料庫

Local MOD Browser 是一個面向 Windows 的本地 MOD 目錄瀏覽器、資料工作臺和 AI 協作平臺。
它不試圖替你“下載更多內容”，而是把你已經擁有、已經整理或明確授權使用的目錄後設資料，
轉換成一個可以搜尋、篩選、比較、收藏、編輯和持續維護的本地系統。

如果你曾經遇到過這些問題，它就是為你準備的：

- 下載過一些 MOD，卻記不清各自的功能或當初的用途，需要藉助資料庫已有的摘要、功能說明與標籤重新找回上下文。
- MOD 分散在多個硬碟、多個遊戲和多個備份目錄裡，想找一個檔案要翻很久。
- 同一個 MOD 有多個版本或副本，無法快速確認差異，也不敢隨便覆蓋原檔案。
- 瀏覽器收藏、翻譯進度、作者資訊和檔案清單彼此分離，重新安裝後很難恢復。
- 想讓 AI 幫忙整理資料，卻不希望把本地路徑、庫存或資料庫上傳到第三方服務。
- 批次編輯或翻譯中途停止後，不希望留下半條記錄、重複提交或無法解釋的狀態。

它提供一個清晰的本地閉環：

```text
你的目录元数据 → 索引与搜索 → 详情 / 标签 / 文件比较 → 收藏与搭配
                                      ↓
                          资料修订 / 翻译任务 / 可恢复批处理
                                      ↓
                         网页、CLI、MCP 共用同一套本地 API
```

當前公開原始碼支援搭配備註，以及 `function`、`details`、`tags` 等 MOD 資料欄位的修訂；這不等於已有獨立的“每個 MOD 的下載原因”筆記欄位。找回上下文依賴已有或由你補充的資訊，不會自動重建未記錄的原始動機。

<a id="先看成品再决定要不要安装"></a>

## 先看成品，再決定要不要安裝

這些截圖來自儲存庫內的 **8 條純虛構 Demo 記錄**，不包含真實 MOD、遊戲素材或第三方站點資料。
它們展示的是公開版啟動後的真實介面，而不是設計稿：

![公開 Demo 的資料卡片與篩選介面](../assets/demo-browse.png)

![公開 Demo 的詳情面板](../assets/demo-detail.png)

![公開 Demo 的關鍵字搜尋結果](../assets/demo-search.png)

![公開 Demo 的窄螢幕佈局](../assets/demo-mobile.png)

完整的可重現操作步驟見 [`docs/demo-walkthrough.md`](../demo-walkthrough.md)。

<a id="用户提供的实际使用截图"></a>

### 使用者提供的實際使用截圖

下面這組圖片來自使用者自己的本地資料庫，展示資料較多時的瀏覽、篩選和詳情介面。它們不是儲存庫附帶的資料，也不是上方八條虛構記錄的可重現 Demo。圖片中的條目數量、遊戲數量和縮圖僅反映截圖當時的使用者環境，不代表安裝本專案後會獲得這些內容。

![實際使用：多遊戲 MOD 資料庫](../assets/real-use/library-overview.png)

*多遊戲資料庫的卡片瀏覽介面。*

![實際使用：按用途篩選](../assets/real-use/purpose-filters.png)

*按用途縮小瀏覽範圍，保留卡片與篩選條件的上下文。*

![實際使用：MOD 詳情側欄](../assets/real-use/mod-detail-panel.png)

*在當前瀏覽頁旁檢視單個條目的詳情。*

另三張截圖：[檔案與變體](../assets/real-use/files-and-variants.png)、[AI 與任務中心](../assets/real-use/ai-task-center.png)、[下載中心](../assets/real-use/download-center.png)。

完整的六張截圖與狀態說明見[實際使用圖集](../real-use-gallery.md)。其中 AI 與任務中心、下載中心僅記錄使用者本地介面的可見狀態；截圖不證明任務或下載成功，也不證明相同功能已包含在當前公開原始碼或發行版中。

截圖內的遊戲、MOD 名稱及縮圖可能涉及第三方權利，不因展示在本儲存庫中而適用專案程式碼的 MIT 授權條款。圖集不提供相關 MOD、遊戲素材或原始資料庫的下載，也不構成對第三方內容的再使用授權。

<a id="30-秒判断它是不是你需要的工具"></a>

### 30 秒判斷它是不是你需要的工具

| 如果你想要…… | Local MOD Browser 的答案 |
| --- | --- |
| 把多個遊戲、多個硬碟的 MOD 放進同一個搜尋入口 | 設定多個本地來源，統一建立可查詢索引 |
| 記起下載過的 MOD 有什麼用 | 回看已有摘要、功能說明與標籤，並手動把計畫記入搭配備註 |
| 只挑選某個 MOD 的一個準確檔案 | 詳情頁提供檔案級比較與精確選擇，不預設整套加入搭配 |
| 讓翻譯或資料整理可以暫停後繼續 | 分段任務、租約、回執、事件遊標與恢復流程 |
| 讓 AI 幫忙，但不上傳私人庫存 | 本地 HTTP / CLI / MCP，共享同一契約，預設只監聽回環位址 |
| 遷移系統或升級後還能找回自己的工作 | 配對備份、恢復記錄、版本歷史與穩定資源身分 |

<a id="它适合谁"></a>

### 它適合誰？

- 有多個遊戲、多個 MOD 來源或長期積累的個人玩家。
- 需要反覆查詢、比較、翻譯、整理 MOD 資料的內容創作者和維護者。
- 想讓 AI 協助做資料工作，但希望資料留在自己的電腦上的使用者。
- 喜歡可重現、可檢查、能恢復，而不是“點一下然後祈禱”的自動化工具的人。

<a id="它不是什么"></a>

### 它不是什麼？

它不是 MOD 下載站、安裝器、破解工具或遠端託管服務。它也不會替你判斷某個 MOD 是否
安全、相容或獲得授權；它負責把你已經擁有且有權使用的資料組織好，讓每次修改都更可見、
更可控。

![使用前後對比：從散落資料夾到本地資料庫](../assets/before-after.svg)

> English summary: Local MOD Browser is a privacy-first, local-only catalog and
> workflow platform for Windows. It indexes metadata supplied by the user and
> provides a browser UI, CLI and optional MCP adapter over one local API. It does
> not download, redistribute, install or execute MOD files.

<a id="你会得到什么"></a>

## 你會得到什麼

<a id="一个真正适合长期使用的-mod-浏览器"></a>

### 一個真正適合長期使用的 MOD 瀏覽器

- 按遊戲、關鍵字、組合標籤、翻譯狀態、作者、日期和檔案資訊快速篩選。
- 在列表、詳情和歷史記錄之間保持穩定導航，不需要反覆回到資料夾裡尋找上下文。
- 檢視圖片、作者正文、檔案清單和來源連結；比較具體檔案副本，而不是只比較 MOD 名稱。
- 收藏重要條目，儲存可匯入、可匯出的搭配清單，方便重灌系統或遷移目錄後繼續工作。
- 桌面寬螢幕和窄螢幕都可用；複雜篩選會收納，重要結果優先呈現。

<a id="一套面向资料维护的工作台"></a>

### 一套面向資料維護的工作臺

- 資料修改先經過 `preview`，確認後再 `apply`，減少誤改和批次操作風險。
- 翻譯內容按欄位和分段管理，支援批次、進度、品質檢查、停止、恢復和冪等重放。
- 背景任務擁有租約、續租、交接和事件遊標；換一個 AI 或重新開啟頁面也能接著做。
- 所有重要寫入都有穩定冪等鍵和權威回執，網路中斷後可以先查詢結果，再決定是否重試。
- SQLite 使用 WAL 與 FULL 同步，配套恢復記錄和成對備份，優先保護資料完整性。

<a id="一个可被-ai-正确使用的本地平台"></a>

### 一個可被 AI 正確使用的本地平臺

- 網頁、CLI 和可選 MCP 介面卡共享同一套契約，不需要 AI 模擬點選網頁。
- 70 項穩定操作覆蓋搜尋、詳情、資料修訂、收藏、搭配、翻譯和任務管理。
- 五條確定性工作流幫助 AI 分階段完成“查詢 → 核對 → 修改 → 復讀 → 彙報”。
- 本地 API 預設只監聽 `127.0.0.1`；服務不呼叫通用模型，也不把資料自動傳送到雲端。
- 發生異常時客戶端只收到請求 ID，本機診斷記錄單獨儲存，避免把路徑和堆疊洩露給呼叫方。

<a id="核心能力一览"></a>

## 核心能力一覽

| 場景 | 能力 | 適合解決的問題 |
| --- | --- | --- |
| 找資料 | 全文搜尋、分頁、組合標籤、作者/日期/翻譯狀態篩選 | “我知道它大概是什麼，但記不清放在哪” |
| 看細節 | 詳情、圖片、來源連結、檔案清單、歷史修訂 | “這個版本到底改了什麼” |
| 做選擇 | 精確檔案比較、收藏、搭配匯入匯出 | “我只想保留這一份，不想誤選整套檔案” |
| 改資料 | 預覽—提交、版本控制、欄位白名單、歷史恢復 | “批次整理時也要能回滾” |
| 做翻譯 | 分段任務、品質門檻、暫停/恢復、冪等回執 | “長文字中斷後不要從頭開始” |
| 讓 AI 協作 | HTTP、CLI、MCP、租約、交接、事件遊標 | “讓不同助手安全接力” |
| 守住資料 | WAL/FULL、配對備份、恢復記錄、生命週期鎖 | “升級或崩潰後仍能恢復” |

<a id="安全边界与隐私设计"></a>

## 安全邊界與隱私設計

Local MOD Browser 的邊界非常明確：

- **只索引你提供的後設資料。** 儲存庫不附帶使用者的原始 MOD 庫、資料庫、備份或匯出包。使用者提供的精選介面截圖單列為文件展示，不作為測試資料或內容分發。
- **不下載、不再分發、不安裝、不執行 MOD。** 它是資料管理工具，不是 MOD 下載器或安裝器。
- **預設只在本機監聽。** 服務繫結 `127.0.0.1`，不設計為區域網或公網服務。
- **不強制繫結第三方帳號。** 可選 MCP 介面卡只是本地協議入口，不會自動呼叫遠端模型。外部 AI 客戶端可能把讀取到的資料傳送給其服務商；連線前請核對客戶端設定與授權範圍。
- **第三方資料由你負責授權。** 使用任何站點或服務時，請遵守其服務條款、API 政策和內容許可。

儲存庫還提供 [安全政策](../../SECURITY.md)、[貢獻指南](../../CONTRIBUTING.md) 和
[第三方宣告](../../THIRD_PARTY_NOTICES.md)。執行時、資料庫、權杖、診斷記錄和測試產物的預設路徑已加入
`.gitignore`，以降低誤提交風險；這不保護已跟蹤檔案、強制新增的檔案或放在其他位置的資料。提交前仍應檢查暫存區。

<a id="支持范围"></a>

## 支援範圍

- Windows 10/11 x64。
- 固定執行時：CPython 3.13.15 x64 與 SQLite 3.53.4。
- 首次安裝需要聯網下載並校驗固定執行時；引導指令碼由系統 Python 執行。
- 執行時來源、雜湊和授權條款見 [`runtime-lock.json`](../../runtime-lock.json)。
- Linux 和 macOS 當前不在支援範圍內；核心服務依賴 Python 標準庫，不需要額外後端框架。

<a id="五分钟开始使用"></a>

## 五分鐘開始使用

<a id="1-获取代码并准备本地配置"></a>

### 1. 獲取程式碼並準備本地設定

```powershell
git clone https://github.com/son-gladyso/Local-Mod-Browser.git
cd Local-Mod-Browser
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
```

<a id="2-安装固定运行时并启动"></a>

### 2. 安裝固定執行時並啟動

```powershell
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

也可以雙擊儲存庫裡的 `启动MOD浏览器.cmd`。啟動器會輸出本機地址；開啟後即可檢視虛構示範
目錄和空庫流程。首次啟動不需要準備真實 MOD 庫。

如果你只想下載當前公開原始碼，可直接使用 [v2.5.2 Release](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2)
中的 `Local-Mod-Browser-2.5.2-source.zip`，旁邊的 `SHA256SUMS.txt` 可用於校驗檔案完整性。

<a id="3-接入自己的目录"></a>

### 3. 接入自己的目錄

編輯被 Git 忽略的 `data\sources.json`：

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

每個 `outputDir` 放置一個 `catalog-data.json`。相對路徑以 `sources.json` 所在目錄為基準；
也可以設定 `LOCAL_MOD_BROWSER_SOURCES` 指向另一份設定。完整示例見
[`config/sources.example.json`](../../config/sources.example.json) 和
[`examples/demo-game/catalog-data.json`](../../examples/demo-game/catalog-data.json)。

<a id="4-检查服务与本地-api"></a>

### 4. 檢查服務與本地 API

```powershell
.\.runtime\python.exe -X utf8 ai.py doctor
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
```

開啟 `/api/docs` 可以檢視機器可讀契約；開啟 `/api/health` 可以確認執行時、資料庫和服務狀態。

<a id="第一次运行怎样算走通了"></a>

## 第一次執行，怎樣算走通了？

先用儲存庫自帶的虛構記錄，不必匯入自己的資料庫：啟動服務 → 開啟本機地址 → 搜尋一個示例條目 → 開啟詳情 → 回到列表。這個小閉環能幫你確認瀏覽與查詢入口，而不必先整理整個硬碟。

開始前請準備 Windows 10/11 x64、可執行引導指令碼的系統 Python，以及首次下載固定執行時所需的網路。普通使用不要求接入 AI 或 MCP；開發者的測試依賴另見[貢獻指南](../../CONTRIBUTING.md)。

**成功標準：**頁面能顯示虛構目錄，搜尋與詳情可實際操作，`ai.py doctor` 的結果可供核對。僅開啟頁面不等於自己的來源設定、恢復流程或所有平臺操作都已驗收。

<a id="常见问题"></a>

## 常見問題

**下載後為什麼沒有截圖中的龐大資料庫？** 那些是使用者提供的實際使用截圖，不隨專案分發。儲存庫自帶的是八條虛構 Demo 記錄；自己的來源需要另行設定。

**它會自動掃描並理解硬碟上的所有 MOD 嗎？** 不會。當前入口是來源設定與每個 `outputDir` 中的 `catalog-data.json`，不是對任意資料夾的萬能識別。先用[設定樣例](../../config/sources.example.json)核對路徑與後設資料。

**能替我記起當初為什麼下載某個 MOD 嗎？** 已有摘要、功能說明和標籤能幫助你重新判斷用途；你可以修訂資料，並手動在搭配備註中記錄計畫。它不能從檔案自動推斷未記錄的原始動機，本文也不承諾存在獨立的逐 MOD 下載原因欄位。

**為什麼列表為空？** 先核對 `data\sources.json` 是否有效、路徑以哪個設定目錄解析，以及目標 `outputDir` 是否有 `catalog-data.json`。再按[使用者指南](../user-guide.md)檢查服務；不要把私人資料庫直接貼進 Issue。

**必須連線 AI 才能瀏覽嗎？** 不需要。網頁和 CLI 可以直接使用。可選 MCP 是本地介面，不是自動連線雲端模型的開關；你另行選擇的外部客戶端具有自己的資料邊界。

**實拍圖裡的下載中心代表公開版能下載 MOD 嗎？** 不能這樣判斷。實拍記錄的是使用者本地介面，其中下載列表為空、Nexus 未連線。當前公開版仍按本文的“不下載、不安裝、不執行 MOD”邊界介紹。

**能在其他裝置或公網存取嗎？** 預設只監聽 `127.0.0.1`，不把它當作 LAN 或公網服務部署。Windows 以外平臺當前也不在支援範圍內。

<a id="按你要改的部分进入源码"></a>

### 按你要改的部分進入原始碼

- 瀏覽與互動：從 `static/` 入手，驗證列表、詳情、空/錯誤狀態及窄螢幕行為。
- 來源與檢索：從 `catalog.py` 和設定樣例入手，用合成目錄覆蓋有效與無效輸入。
- 平臺操作：一起閱讀 `contracts.py`、`platform_api.py` 與對應測試，保持 HTTP、CLI、MCP 一致。
- 持久化或背景任務：先讀[架構說明](../architecture.md)，覆蓋中斷、重試與恢復，不以犧牲資料持久性換取速度。

各類改動的命令和 PR 要求見[貢獻指南](../../CONTRIBUTING.md)；現有入門任務在[版本、路線與貢獻](#版本路线与贡献)。


<a id="cli-与-ai-协作"></a>

## CLI 與 AI 協作

CLI 是指令碼和 AI 的穩定入口，不需要模擬滑鼠操作：

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

建議的安全工作流是：

1. 先讀取能力和介面說明，確認當前版本支援的操作。
2. 先搜尋和讀取資源，再提交 `preview`，不要憑陣列順序猜測檔案身分。
3. 檢查預覽返回的資源 ID、版本和差異，再使用穩定 `idempotencyKey` 提交。
4. 對背景任務等待真實終態，核對業務回讀和權威回執，不把 `queued` 當作完成。
5. 中斷後先查回執和事件遊標，再繼續、交接或重試。

詳細說明：[`docs/user-guide.md`](../user-guide.md)、
[`docs/ai-platform-guide.md`](../ai-platform-guide.md)、
[`docs/architecture.md`](../architecture.md)。

<a id="验证与质量门槛"></a>

## 驗證與品質門檻

專案不是“能啟動就算完成”。公開版保留了可重現的合成驗收指令碼：

```powershell
# Python 回归
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v

# 启动、协作与契约
.\.runtime\python.exe -X utf8 tests\startup_acceptance.py
.\.runtime\python.exe -X utf8 tests\collaboration_acceptance.py
python -m pip install jsonschema==4.26.0
python -X utf8 tests\contract_audit.py --fixture

# 前端语法
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
```

瀏覽器驗收另需 `npm install` 及 Playwright 瀏覽器。CI 在 Windows runner 上自動執行固定執行時
安裝、Python 迴歸、契約審計和 JavaScript 檢查；詳見 [貢獻指南](../../CONTRIBUTING.md)。

<a id="项目结构"></a>

## 專案結構

```text
Local-Mod-Browser/
├─ server.py                    本地 HTTP 服务与统一错误边界
├─ platform_api.py              70 项平台操作与业务规则
├─ contracts.py                 HTTP/CLI/MCP 共用契约与 Schema
├─ catalog.py                   来源配置、索引和查询投影
├─ ai.py                        面向脚本和 AI 的 CLI
├─ mcp_adapter.py               可选的本地 MCP 入口
├─ static/                      浏览器界面
├─ tests/                       回归、契约、启动、协作与性能验收
├─ tools/bootstrap_runtime.py   固定运行时安装与校验
└─ docs/                        用户、AI 平台和架构说明
```

<a id="版本路线与贡献"></a>

## 版本、路線與貢獻

當前公開版本為 `v2.5.2`，API 契約為 `2.5.0`。最新方向見 [`ROADMAP.md`](../../ROADMAP.md)；文件、可重現測試、無障礙和小範圍來源設定改進都適合首次貢獻。專案優先關注：

- 讓本地資料整理更快、更容易複核，而不是擴大資料收集範圍。
- 保持 API、CLI 和 MCP 的行為一致，並讓失敗可以解釋、可以恢復。
- 用合成資料和可重現驗收保護資料安全；不把私人庫存作為公開測試樣本。
- 在明確的內容授權和第三方條款範圍內擴充來源支援。

歡迎提交 Issue、改進文件和 Pull Request。請先閱讀 [CONTRIBUTING.md](../../CONTRIBUTING.md)，
不要提交個人路徑、庫存、資料庫、截圖中的權杖或任何未獲授權的第三方內容。外部改動需經過審查；合併到 `main` 前須滿足 CI、Code Owner 批准、討論解決、隱私檢查與針對性測試要求。

如果它解決了你的一個真實問題，歡迎點一個 Star、分享給同樣被“MOD 資料夾失控”困擾的人，
或者提交一個具體的 Issue。對開源專案來說，一條清晰的使用回饋比一句“看起來不錯”更有幫助。

<a id="从一个小改进入手"></a>

### 從一個小改進入手

第一次參與，可以從這些已有任務選擇一個：

- [首次執行 FAQ（#3）](https://github.com/son-gladyso/Local-Mod-Browser/issues/3)：補充執行時安裝、來源設定和目錄檔案缺失的排查步驟。
- [來源設定文件與校驗（#2）](https://github.com/son-gladyso/Local-Mod-Browser/issues/2)：說明欄位與相對路徑行為，並用合成設定覆蓋錯誤情況。
- [空狀態與錯誤狀態的無障礙提示（#1）](https://github.com/son-gladyso/Local-Mod-Browser/issues/1)：讓鍵盤和螢幕閱讀器使用者也能知道下一步做什麼。

先檢查任務的最新討論與狀態，再說明你準備處理的範圍。小的文件修正可以直接提交 PR；較大功能、資料模型或來源適配改動，請先按貢獻指南討論。無需提供自己的 MOD 庫來參與。

<a id="许可证"></a>

## 授權條款

專案程式碼使用 [MIT License](../../LICENSE)。第三方執行時和可選依賴的說明見
[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)。MIT 許可不授予任何 MOD、遊戲素材、
站點資料、作者正文或其他第三方內容的權利。

