# Local MOD Browser

[简体中文](../../README.md) · [English](../../README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)

이 언어 선택은 README 번역에만 적용됩니다. 앱 화면이나 연결된 모든 가이드가 다국어를 지원한다는 뜻은 아닙니다.

<p align="center"><img src="../assets/logo-small.png" alt="Local MOD Browser 로고" width="112"></p>

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![API contract](https://img.shields.io/badge/API%20contract-2.5.0-6f42c1)
[![CI](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml/badge.svg)](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml)

> **MOD 라이브러리가 계속 커지는 폴더 더미로만 남을 필요는 없습니다.**
>
> 로컬에서 검색하고 복구하며 AI와 협업할 수 있는 작업 공간으로, “그 MOD가 있었던 것 같은데”를 “몇 초 만에 찾아 확인하고 작업을 이어 갈 수 있어”로 바꿉니다.
>
> **MOD를 다운로드했지만 무슨 기능인지, 왜 받고 싶었는지 잊었나요?** 기존 요약, 기능 설명, 태그가 맥락을 되찾는 단서가 됩니다. 앞으로의 사용 계획은 구성 세트 메모에 직접 기록할 수 있습니다. 브라우저가 원래 다운로드 의도를 자동으로 추론하는 것은 아닙니다.

[시작하기](#five-minute-quick-start) · [v2.5.2 다운로드](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2) · [AI와 CLI](#ai-and-cli) · [보안 경계](#privacy-and-security) · [이슈 작성](https://github.com/son-gladyso/Local-Mod-Browser/issues)

## 흩어진 MOD를 유용한 개인 자료실로

Local MOD Browser는 Windows용 로컬 MOD 목록 브라우저, 메타데이터 작업 공간, AI 협업 플랫폼입니다. 콘텐츠를 더 다운로드해 주는 대신, 직접 소유·관리하거나 명확하게 이용을 허가받은 디렉터리의 메타데이터를 검색, 필터링, 비교, 즐겨찾기, 편집, 번역하고 꾸준히 관리할 수 있는 로컬 시스템으로 정리합니다.

다음 문제가 익숙하다면 도움이 됩니다.

- 여러 드라이브, 게임, 백업 폴더에 MOD가 흩어져 있어 파일 하나를 찾는 데 오래 걸립니다.
- 받아 둔 MOD가 어떤 기능인지, 왜 필요했는지 기억나지 않습니다. 목록에 있는 요약, 기능 설명, 태그로 파일과 용도를 다시 연결하고 싶습니다.
- 같은 MOD의 여러 버전이나 사본을 빨리 비교하기 어렵고, 원본을 실수로 덮어쓰고 싶지 않습니다.
- 즐겨찾기, 번역 진행 상황, 제작자 정보, 파일 목록이 따로 있어 재설치 뒤 복구하기 어렵습니다.
- AI의 정리 도움은 받고 싶지만 서비스가 로컬 경로, 보유 목록, 데이터베이스를 제삼자에게 업로드하기는 원하지 않습니다. 외부 AI 클라이언트에는 자체 데이터 공유 동작이 있습니다.
- 일괄 편집이나 번역이 중단되어도 불완전한 기록, 중복 제출, 설명할 수 없는 상태가 남지 않았으면 합니다.

명확한 로컬 작업 흐름을 제공합니다.

```text
디렉터리 메타데이터 → 색인과 검색 → 상세 / 태그 / 파일 비교 → 즐겨찾기 / 구성 세트
                                        ↓
                         자료 수정 / 번역 작업 / 재개 가능한 일괄 처리
                                        ↓
                         웹, CLI, MCP가 같은 로컬 API 공유
```

현재 공개 소스는 구성 세트 메모와 MOD의 `function`, `details`, `tags` 같은 필드 편집을 지원합니다. MOD마다 독립적인 “다운로드 이유” 메모 필드가 있다는 주장은 아닙니다. 맥락 복구에는 이미 있거나 직접 보충한 정보가 필요하며, 기록되지 않은 원래 의도를 자동으로 재구성하지 않습니다.

## 설치 전에 실제 화면 보기

다음 스크린샷은 저장소에 포함된 **완전히 가상인 Demo 기록 8개**를 사용합니다. 실제 MOD, 게임 에셋, 제삼자 사이트의 데이터는 포함하지 않습니다. 디자인 시안이 아니라 공개 버전을 실행한 실제 화면입니다.

![공개 데모 목록과 필터](../assets/demo-browse.png)

![공개 데모 상세 패널](../assets/demo-detail.png)

![공개 데모 키워드 검색](../assets/demo-search.png)

![공개 데모 좁은 화면 레이아웃](../assets/demo-mobile.png)

재현 가능한 전체 절차는 [`docs/demo-walkthrough.md`](../demo-walkthrough.md)를 참고하세요.

### 사용자가 제공한 실제 사용 스크린샷

다음 이미지는 사용자의 개인 로컬 라이브러리에서 많은 자료를 탐색하고 필터링하며 상세 내용을 확인하는 모습입니다. 배포되는 데이터도, 위의 가상 기록 8개로 재현하는 데모도 아닙니다. 항목 수, 게임 수, 썸네일은 촬영 당시 사용자 환경만 반영하며 설치 시 제공되는 콘텐츠를 뜻하지 않습니다.

![실제 사용: 여러 게임의 MOD 라이브러리](../assets/real-use/library-overview.png)

*여러 게임의 라이브러리를 카드 형태로 탐색합니다.*

![실제 사용: 용도별 필터](../assets/real-use/purpose-filters.png)

*카드와 필터 조건의 맥락을 유지하며 용도별로 범위를 좁힙니다.*

![실제 사용: MOD 상세 패널](../assets/real-use/mod-detail-panel.png)

*현재 목록 옆에서 개별 항목의 상세 내용을 확인합니다.*

나머지 3장: [파일과 변형](../assets/real-use/files-and-variants.png), [AI 및 작업 센터](../assets/real-use/ai-task-center.png), [다운로드 센터](../assets/real-use/download-center.png).

전체 6장과 상태 설명은 [실제 사용 갤러리](../real-use-gallery.md#english)를 참고하세요. AI 및 작업 센터와 다운로드 센터 이미지는 사용자 로컬 화면에 보인 상태만 기록합니다. 작업이나 다운로드가 성공했다거나 동일한 기능이 현재 공개 소스 또는 배포판에 포함되어 있음을 증명하지 않습니다.

게임명, MOD 이름, 썸네일에는 제삼자 권리가 적용될 수 있습니다. 저장소에 표시된다고 MIT 라이선스가 적용되는 것은 아닙니다. 갤러리는 해당 MOD, 게임 에셋, 원본 라이브러리를 배포하지 않으며 제삼자 콘텐츠의 재사용 권한도 부여하지 않습니다.

### 30초 안에 필요한 도구인지 판단하기

| 원하는 것 | Local MOD Browser의 대응 |
| --- | --- |
| 여러 게임과 드라이브의 MOD를 한곳에서 검색 | 여러 로컬 소스를 설정해 통합 검색 색인 생성 |
| 다운로드한 MOD의 용도 다시 확인 | 기존 요약, 기능 설명, 태그를 살피고 구성 세트 메모에 계획을 직접 기록 |
| MOD에서 정확히 한 파일만 선택 | 파일 단위 비교와 명시적 선택. 기본적으로 전체 세트를 구성 세트에 넣지 않음 |
| 번역이나 자료 정리를 멈췄다가 재개 | 분할 작업, 임대, 처리 확인서, 이벤트 커서, 복구 |
| 서비스가 개인 보유 목록을 업로드하지 않으면서 AI 활용 | 같은 계약의 로컬 HTTP / CLI / MCP, 기본 루프백 전용 리스너 |
| 이동이나 업데이트 뒤 작업 복구 | 쌍으로 된 백업, 복원 저널, 버전 이력, 안정적인 리소스 식별자 |

### 누구에게 적합한가요?

- 여러 게임과 MOD 출처를 사용하거나 오랫동안 파일을 모아 온 플레이어.
- MOD 자료를 반복해서 찾고 비교하고 번역하고 정리하는 제작자와 관리자.
- 자신의 컴퓨터에 있는 데이터를 통제하면서 AI의 도움을 받고 싶은 사용자.
- “클릭하고 잘되길 비는” 방식보다 재현·검사·복구 가능한 자동화를 선호하는 사람.

### 이 도구가 아닌 것

MOD 다운로드 사이트, 설치 프로그램, 크랙 도구, 원격 호스팅 서비스가 아닙니다. MOD의 안전성, 호환성, 이용 권한도 대신 판단하지 않습니다. 이미 보유하고 이용 권한이 있는 자료를 정리해 변경을 더 잘 확인하고 통제하도록 돕습니다. MOD 파일을 다운로드, 재배포, 설치, 실행하지 않습니다.

![사용 전후: 흩어진 폴더에서 로컬 자료실로](../assets/before-after.svg)

## 제공하는 기능

### 오래 사용하기 위한 MOD 브라우저

- 게임, 키워드, 조합 태그, 번역 상태, 제작자, 날짜, 파일 정보로 빠르게 필터링합니다.
- 목록, 상세 내용, 이력 사이를 안정적으로 이동해 맥락을 찾으러 폴더로 반복해서 돌아갈 필요를 줄입니다.
- 이미지, 제작자 본문, 파일 목록, 출처 링크를 확인합니다. MOD 이름만이 아니라 구체적인 파일 사본을 비교합니다.
- 중요한 항목을 즐겨찾기에 넣고 가져오기·내보내기가 가능한 구성 세트를 저장해 재설치나 디렉터리 이동 후 작업을 이어 갑니다.
- 넓거나 좁은 화면 모두 지원합니다. 복잡한 필터는 접고 중요한 결과를 우선 표시합니다.

### 메타데이터 유지·관리 작업 공간

- `apply` 전에 `preview`로 변경을 확인해 실수와 일괄 작업 위험을 줄입니다.
- 번역을 필드와 구간 단위로 관리하고 배치, 진행 상황, 품질 검사, 중지·재개, 멱등 재실행을 지원합니다.
- 백그라운드 작업은 임대, 갱신, 인계, 이벤트 커서를 지원해 다른 AI나 다시 연 페이지에서 이어 갈 수 있습니다.
- 중요한 쓰기에는 안정적인 멱등 키와 권위 있는 처리 확인서가 있습니다. 연결이 끊긴 뒤에는 결과부터 조회하고 재시도 여부를 판단합니다.
- SQLite의 WAL과 FULL 동기화, 복원 저널, 쌍으로 된 백업으로 데이터 무결성을 우선합니다.

### AI가 올바르게 사용할 수 있는 로컬 플랫폼

- 웹, CLI, 선택적 MCP 어댑터가 같은 계약을 사용하므로 AI가 브라우저 클릭을 흉내 낼 필요가 없습니다.
- 검색, 상세, 자료 수정, 즐겨찾기, 구성 세트, 번역, 작업 관리를 70개의 안정적인 연산으로 제공합니다.
- 5개의 결정적 워크플로가 찾기→확인→변경→다시 읽기→보고를 단계별로 안내합니다.
- 로컬 API는 기본적으로 `127.0.0.1`에서만 수신합니다. 서비스는 범용 모델을 호출하거나 데이터를 자동으로 클라우드에 보내지 않습니다.
- 예외 발생 시 클라이언트에는 요청 ID만 전달합니다. 로컬 진단 로그를 따로 저장해 경로와 스택 추적이 호출자에게 노출되지 않도록 합니다.

## 핵심 기능 한눈에 보기

| 상황 | 기능 | 해결하는 문제 |
| --- | --- | --- |
| 자료 찾기 | 전문 검색, 페이지 나누기, 조합 태그, 제작자·날짜·번역 상태 필터 | “대략 기억은 나지만 어디 있는지 모르겠다” |
| 상세 확인 | 상세, 이미지, 출처 링크, 파일 목록, 수정 이력 | “이 버전에서 무엇이 바뀌었나?” |
| 선택하기 | 정확한 파일 비교, 즐겨찾기, 구성 세트 가져오기·내보내기 | “이 사본만 필요한데 전체를 잘못 선택하고 싶지 않다” |
| 자료 수정 | 미리 보기·적용, 버전 관리, 필드 허용 목록, 이력 복원 | “일괄 정리도 되돌릴 수 있어야 한다” |
| 번역하기 | 분할 작업, 품질 기준, 중지·재개, 멱등 처리 확인서 | “긴 글이 중단돼도 처음부터 다시 하고 싶지 않다” |
| AI 협업 | HTTP, CLI, MCP, 임대, 인계, 이벤트 커서 | “다른 어시스턴트가 안전하게 이어서 해야 한다” |
| 데이터 보호 | WAL/FULL, 쌍 백업, 복원 저널, 수명 주기 잠금 | “업데이트나 충돌 뒤에도 복구하고 싶다” |

<a id="privacy-and-security"></a>
## 개인정보 보호와 보안 경계

Local MOD Browser의 경계는 명확합니다.

- **제공한 메타데이터만 색인화합니다.** 저장소에 사용자의 원본 MOD 라이브러리, 압축 파일, 데이터베이스, 백업, 내보내기 파일, 런타임 토큰은 포함되지 않습니다. 선별된 사용자 제공 스크린샷은 별도 설명 자료이며 테스트 데이터나 콘텐츠 다운로드가 아닙니다.
- **MOD를 다운로드, 재배포, 설치, 실행하지 않습니다.** 메타데이터 관리 도구이지 다운로더나 설치 프로그램이 아닙니다.
- **기본적으로 로컬에서만 수신합니다.** `127.0.0.1`에 바인딩하며 LAN이나 공개 서비스로 설계되지 않았습니다.
- **제삼자 계정은 필수가 아닙니다.** 선택적 MCP는 로컬 프로토콜 진입점일 뿐 원격 모델을 자동 호출하지 않습니다. 외부 AI 클라이언트는 읽은 데이터를 제공업체로 보낼 수 있으므로 연결 전에 클라이언트 설정과 허가 범위를 확인하세요.
- **제삼자 데이터 이용 허가는 사용자의 책임입니다.** 각 사이트나 서비스의 약관, API 정책, 콘텐츠 라이선스를 지키세요.

[보안 정책](../../SECURITY.md), [기여 가이드](../../CONTRIBUTING.md), [제삼자 고지](../../THIRD_PARTY_NOTICES.md)를 확인하세요. 런타임, 데이터베이스, 토큰, 진단 로그, 내보내기, 테스트 산출물의 기본 경로는 `.gitignore`에 넣어 실수로 커밋할 위험을 줄였습니다. 이미 추적 중인 파일, 강제 추가한 파일, 다른 위치의 데이터는 보호되지 않습니다. 커밋 전에 스테이징한 변경을 확인하세요.

## 지원 환경

- Windows 10/11 x64.
- 고정 런타임: CPython 3.13.15 x64와 SQLite 3.53.4.
- 첫 설치에는 고정 런타임을 다운로드·검증할 네트워크가 필요합니다. 부트스트랩 스크립트는 시스템 Python으로 실행합니다.
- 런타임 출처, 해시, 라이선스는 [`runtime-lock.json`](../../runtime-lock.json)에 있습니다.
- Linux와 macOS는 현재 지원하지 않습니다. 핵심 서비스는 Python 표준 라이브러리를 사용하며 별도 백엔드 프레임워크가 필요하지 않습니다.

<a id="five-minute-quick-start"></a>
## 5분 만에 시작하기

### 1. 코드 받기와 로컬 설정 준비

```powershell
git clone https://github.com/son-gladyso/Local-Mod-Browser.git
cd Local-Mod-Browser
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
```

### 2. 고정 런타임 설치와 실행

```powershell
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

저장소의 `启动MOD浏览器.cmd`를 더블 클릭해도 됩니다. 실행기가 출력하는 로컬 URL을 열어 가상 데모 목록과 빈 라이브러리 작업 흐름을 확인하세요. 처음 실행할 때 실제 MOD 라이브러리는 필요하지 않습니다.

공개 소스를 바로 받으려면 [v2.5.2 Release](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2)의 `Local-Mod-Browser-2.5.2-source.zip`을 사용하세요. 함께 제공되는 `SHA256SUMS.txt`로 압축 파일의 무결성을 검증할 수 있습니다.

### 3. 내 목록 연결하기

Git에서 무시하는 `data\sources.json`을 편집합니다.

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

각 `outputDir`에 `catalog-data.json`을 두세요. 상대 경로는 `sources.json`이 있는 디렉터리를 기준으로 해석합니다. `LOCAL_MOD_BROWSER_SOURCES`로 다른 설정을 가리킬 수도 있습니다. [`config/sources.example.json`](../../config/sources.example.json)과 [`examples/demo-game/catalog-data.json`](../../examples/demo-game/catalog-data.json)을 참고하세요.

### 4. 서비스와 로컬 API 확인

```powershell
.\.runtime\python.exe -X utf8 ai.py doctor
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
```

`/api/docs`에서 기계가 읽을 수 있는 계약을, `/api/health`에서 런타임·데이터베이스·서비스 상태를 확인하세요.

## 첫 실행이 성공했는지 어떻게 확인하나요?

내 라이브러리를 가져오기 전에 가상 기록으로 시작하세요. 서비스 실행→로컬 URL 열기→샘플 검색→상세 열기→목록으로 돌아가기. 이 짧은 흐름으로 전체 드라이브를 정리하기 전에 탐색과 검색을 확인할 수 있습니다.

Windows 10/11 x64, 부트스트랩 스크립트를 실행할 시스템 Python, 최초 런타임 다운로드를 위한 네트워크를 준비하세요. 일반 사용에는 AI나 MCP가 필요하지 않습니다. 개발자 테스트 의존성은 [기여 가이드](../../CONTRIBUTING.md)에 있습니다.

**성공 기준:** 가상 목록이 표시되고 검색과 상세 보기를 실제로 사용할 수 있으며 `ai.py doctor` 결과를 확인할 수 있어야 합니다. 페이지가 열렸다는 사실만으로 내 소스 설정, 복구 동작, 모든 플랫폼 연산이 검증된 것은 아닙니다.

## 자주 묻는 질문

**다운로드했는데 스크린샷의 큰 라이브러리가 없는 이유는 무엇인가요?** 사용자 환경의 실제 화면이며 데이터는 배포하지 않습니다. 저장소에 포함된 것은 가상 Demo 기록 8개입니다. 자신의 소스는 별도로 설정하세요.

**드라이브의 모든 MOD를 자동으로 스캔하고 이해하나요?** 아닙니다. 입력은 소스 설정과 각 `outputDir`의 `catalog-data.json`입니다. 임의 폴더를 만능으로 해석하는 도구가 아닙니다. [설정 예시](../../config/sources.example.json)로 경로와 메타데이터를 먼저 확인하세요.

**MOD를 왜 다운로드했는지 기억하도록 도와주나요?** 기존 요약, 기능 설명, 태그로 용도를 다시 살필 수 있습니다. 메타데이터를 수정하거나 구성 세트 메모에 계획을 직접 쓸 수 있습니다. 기록하지 않은 원래 의도를 파일에서 추론하지 못하며, 이 README는 MOD별 다운로드 이유 전용 필드를 약속하지 않습니다.

**목록이 왜 비어 있나요?** `data\sources.json`이 유효한지, 상대 경로의 기준이 되는 설정 디렉터리가 어디인지, 대상 `outputDir`에 `catalog-data.json`이 있는지 확인하세요. 이어서 [사용자 가이드](../user-guide.md)로 서비스를 점검하세요. 개인 데이터베이스를 이슈에 올리지 마세요.

**탐색하려면 AI를 연결해야 하나요?** 아닙니다. 웹과 CLI를 바로 사용할 수 있습니다. 선택적 MCP는 로컬 인터페이스이지 자동 클라우드 모델 연결 스위치가 아닙니다. 선택한 외부 클라이언트에는 별도 데이터 경계가 있습니다.

**실제 사용의 다운로드 센터 화면은 공개 버전이 MOD를 받을 수 있다는 뜻인가요?** 아닙니다. 비어 있는 다운로드 목록과 연결되지 않은 Nexus가 보이는 사용자의 로컬 화면입니다. 공개 버전은 계속 “다운로드, 설치, 실행하지 않음”으로 설명합니다.

**다른 기기나 인터넷에서 접근할 수 있나요?** 기본 수신 주소는 `127.0.0.1`입니다. LAN이나 공개 서비스로 배포하지 마세요. Windows 이외 플랫폼도 현재 지원 범위 밖입니다.

### 바꾸려는 부분에 맞춰 소스 찾기

- 탐색과 상호작용: `static/`부터 살펴보고 목록, 상세, 빈 상태·오류 상태, 좁은 화면 동작을 검증하세요.
- 소스와 검색: `catalog.py`와 설정 예시부터 시작해 합성 목록으로 유효·무효 입력을 테스트하세요.
- 플랫폼 연산: `contracts.py`, `platform_api.py`, 관련 테스트를 함께 읽고 HTTP, CLI, MCP 동작을 일치시키세요.
- 영속성이나 백그라운드 작업: 먼저 [아키텍처 가이드](../architecture.md)를 읽고 중단, 재시도, 복구를 확인하세요. 속도를 위해 내구성을 희생하지 마세요.

명령과 PR 요구 사항은 [기여 가이드](../../CONTRIBUTING.md), 입문 과제는 [로드맵과 기여](#roadmap-and-contributing)에 있습니다.

<a id="ai-and-cli"></a>
## AI와 CLI

CLI는 스크립트와 AI를 위한 안정적인 진입점이며 마우스 조작을 흉내 낼 필요가 없습니다.

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

권장하는 안전한 작업 흐름:

1. 기능 목록과 인터페이스 문서를 읽어 현재 버전이 지원하는 연산을 확인합니다.
2. 리소스를 검색하고 읽은 다음 `preview`를 제출합니다. 배열 순서로 파일 정체성을 추측하지 마세요.
3. 미리 보기의 리소스 ID, 버전, 차이를 확인한 후 안정적인 `idempotencyKey`로 적용합니다.
4. 백그라운드 작업의 실제 종료 상태를 기다리고 업무 데이터 재조회와 권위 있는 처리 확인서를 점검합니다. `queued`는 완료가 아닙니다.
5. 중단 뒤에는 처리 확인서와 이벤트 커서를 확인한 다음 계속 진행하거나 인계하거나 재시도합니다.

[`docs/user-guide.md`](../user-guide.md), [`docs/ai-platform-guide.md`](../ai-platform-guide.md), [`docs/architecture.md`](../architecture.md)를 참고하세요.

## 검증과 품질 기준

시작된다고 프로젝트가 완성된 것은 아닙니다. 공개 버전에는 재현 가능한 합성 인수 테스트 스크립트가 있습니다.

```powershell
# Python 회귀 테스트
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v

# 시작, 협업, 계약
.\.runtime\python.exe -X utf8 tests\startup_acceptance.py
.\.runtime\python.exe -X utf8 tests\collaboration_acceptance.py
python -m pip install jsonschema==4.26.0
python -X utf8 tests\contract_audit.py --fixture

# 프런트엔드 구문
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
```

브라우저 인수 테스트에는 별도로 `npm install`과 Playwright 브라우저가 필요합니다. Windows CI는 고정 런타임 설치, Python 회귀, 계약 감사, JavaScript 검사를 자동 실행합니다. [기여 가이드](../../CONTRIBUTING.md)를 참고하세요.

## 프로젝트 구성

```text
Local-Mod-Browser/
├─ server.py                    로컬 HTTP 서비스와 통합 오류 경계
├─ platform_api.py              70개 플랫폼 연산과 업무 규칙
├─ contracts.py                 HTTP/CLI/MCP 공통 계약과 스키마
├─ catalog.py                   소스 설정, 색인, 질의 투영
├─ ai.py                        스크립트와 AI용 CLI
├─ mcp_adapter.py               선택적 로컬 MCP 진입점
├─ static/                      브라우저 화면
├─ tests/                       회귀, 계약, 시작, 협업, 성능과 장시간 실행 검사
├─ tools/bootstrap_runtime.py   고정 런타임 설치와 검증
└─ docs/                        사용자, AI 플랫폼, 아키텍처 가이드
```

<a id="roadmap-and-contributing"></a>
## 로드맵과 기여

현재 공개 버전은 `v2.5.2`, API 계약은 `2.5.0`입니다. 우선순위는 다음과 같습니다.

- 데이터 수집 범위를 늘리지 않고 로컬 자료 정리를 더 빠르고 검토하기 쉽게 만듭니다.
- API, CLI, MCP의 동작을 일치시키고 실패를 설명하고 복구할 수 있게 합니다.
- 합성 데이터와 재현 가능한 인수 테스트로 데이터를 보호하며 개인 보유 목록을 공개 테스트 자료로 쓰지 않습니다.
- 명확한 콘텐츠 이용 허가와 제삼자 약관의 범위에서 소스 어댑터를 확장합니다.

현재 방향은 [`ROADMAP.md`](../../ROADMAP.md)를 참고하세요. 문서, 재현 가능한 테스트, 접근성, 소규모 소스 설정 개선은 첫 기여로 좋습니다.

이슈, 문서 개선, Pull Request를 환영합니다. 먼저 [CONTRIBUTING.md](../../CONTRIBUTING.md)를 읽고 개인 경로, 보유 목록, 데이터베이스, 스크린샷에 보이는 토큰, 허가받지 않은 제삼자 콘텐츠를 제출하지 마세요. 외부 변경은 검토되며 `main`에 병합하기 전에 CI, Code Owner 승인, 논의 해결, 개인정보 점검, 집중 테스트가 필요합니다.

실제 문제를 해결했다면 Star를 누르거나 MOD 폴더 관리에 어려움을 겪는 사람에게 알리거나 구체적인 이슈를 작성해 주세요. 명확하고 재현 가능한 피드백은 “좋아 보여요”나 모호한 기능 요청보다 도움이 됩니다. 수락한 개선은 공개 이력에서 검토할 수 있습니다.

### 작은 개선부터 시작하기

처음 기여한다면 다음 기존 과제에서 골라 보세요.

- [첫 실행 FAQ (#3)](https://github.com/son-gladyso/Local-Mod-Browser/issues/3): 런타임 설치, 소스 설정, 목록 파일 누락의 문제 해결과 검증 절차를 추가합니다.
- [소스 설정 문서와 검증 (#2)](https://github.com/son-gladyso/Local-Mod-Browser/issues/2): 필드와 상대 경로를 설명하고 합성 설정으로 오류를 테스트합니다.
- [접근성 있는 빈 상태와 오류 상태 (#1)](https://github.com/son-gladyso/Local-Mod-Browser/issues/1): 키보드와 화면 낭독기 사용자가 다음 행동을 알 수 있게 합니다.

범위를 정하기 전에 최신 이슈 논의와 상태를 확인하세요. 작은 문서 수정은 바로 PR로 제출할 수 있습니다. 큰 기능, 데이터 모델, 소스 어댑터 변경은 기여 가이드에 따라 먼저 논의하세요. 기여를 위해 개인 MOD 라이브러리를 제공할 필요는 없습니다.

## 라이선스

프로젝트 코드는 [MIT License](../../LICENSE)를 사용합니다. 제삼자 런타임과 선택적 의존성 고지는 [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)에 있습니다. MIT는 MOD, 게임 에셋, 사이트 데이터, 제작자 본문, 기타 제삼자 콘텐츠의 권리를 부여하지 않습니다.
