# Local MOD Browser

[简体中文](../../README.md) · [English](../../README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · Deutsch · [Português (Brasil)](README.pt-BR.md)

Diese Sprachoptionen übersetzen die README, nicht die Anwendungsoberfläche oder sämtliche verlinkten Anleitungen.

**Versionsstatus (2026-10-20):** Die nächste Version befindet sich in separaten Abnahmetests und ist noch nicht veröffentlicht. Die aktuelle öffentliche Version bleibt `v2.5.2` (API-Vertrag `2.5.0`); die folgenden Installationsschritte, Funktionen und Sicherheitsgrenzen beschreiben diese öffentliche Version. Neue Funktionen des Entwicklungskandidaten oder aus Screenshots lokaler Benutzerumgebungen dürfen nicht als Bestandteil der öffentlichen Version angesehen werden.

<p align="center"><img src="../../docs/assets/logo-small.png" alt="Logo von Local MOD Browser" width="112"></p>

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Lizenz](https://img.shields.io/badge/license-MIT-2ea44f)
![API-Vertrag](https://img.shields.io/badge/API%20contract-2.5.0-6f42c1)
[![CI](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml/badge.svg)](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml)

> **Deine MOD-Bibliothek sollte mehr sein als ein ständig wachsender Haufen von Ordnern.**
>
> Mache aus „Ich weiß noch, dass ich diesen MOD hatte“ ein „Ich kann ihn in Sekunden finden, prüfen und weiterarbeiten“: mit einem lokalen, durchsuchbaren, wiederherstellbaren Arbeitsbereich, der mit KI zusammenarbeiten kann.
>
> **Einen MOD heruntergeladen und später vergessen, wofür du ihn haben wolltest oder was er macht?** Vorhandene Zusammenfassungen, Funktionsbeschreibungen und Tags helfen dir, diesen Zusammenhang wiederzufinden. Zukünftige Pläne kannst du von Hand in Loadout-Notizen festhalten. Der Browser erschließt deine ursprünglichen Downloadgründe nicht automatisch.

[Erste Schritte](#five-minute-quick-start) · [v2.5.2 herunterladen](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2) · [KI und CLI](#ai-and-cli) · [Sicherheitsgrenzen](#privacy-and-security) · [Issue öffnen](https://github.com/son-gladyso/Local-Mod-Browser/issues)

<a id="turn-scattered-mods-into-a-useful-personal-catalog"></a>

## Verstreute MODs in einen nützlichen persönlichen Katalog verwandeln

Local MOD Browser ist ein lokaler MOD-Katalogbrowser, ein Arbeitsbereich für Metadaten und eine Plattform für die Zusammenarbeit mit KI unter Windows. Statt weitere Inhalte für dich herunterzuladen, verwandelt er Metadaten aus Verzeichnissen, die dir gehören, die du pflegst oder zu deren Nutzung du ausdrücklich berechtigt bist, in ein lokales System. Darin kannst du suchen, filtern, vergleichen, favorisieren, bearbeiten, übersetzen und Informationen dauerhaft pflegen.

Er passt zu dir, wenn dir eines dieser Probleme bekannt vorkommt:

- MODs sind über Laufwerke, Spiele und Sicherungsordner verstreut, und die Suche nach einer Datei dauert zu lange.
- Du hast MODs heruntergeladen, weißt aber nicht mehr, was die einzelnen MODs tun oder warum du sie haben wolltest. Bereits im Katalog enthaltene Zusammenfassungen, Funktionsbeschreibungen und Tags helfen dir, Dateien wieder ihrem Zweck zuzuordnen.
- Mehrere Versionen oder Kopien sind schwer zu vergleichen, und du möchtest kein Original versehentlich überschreiben.
- Favoriten, Übersetzungsfortschritt, Autoreninformationen und Dateilisten liegen getrennt vor und lassen sich nach einer Neuinstallation nur schwer wiederherstellen.
- Du möchtest KI-Unterstützung beim Ordnen, ohne dass der Dienst deine lokalen Pfade, Bestandslisten oder Datenbank an Dritte hochlädt. Jeder externe KI-Client hat ein eigenes Verhalten bei der Datenweitergabe.
- Unterbrochene Stapelbearbeitungen oder Übersetzungen sollen keine halb geschriebenen Datensätze, doppelten Übermittlungen oder unerklärlichen Zustände hinterlassen.

Dafür bietet er einen klaren lokalen Ablauf:

```text
Deine Verzeichnismetadaten → Index und Suche → Details / Tags / Dateivergleich → Favoriten / Loadouts
                                                          ↓
                                         Revisionen / Übersetzungsaufträge / fortsetzbare Stapel
                                                          ↓
                                         Browser, CLI und MCP über eine lokale API
```

Der aktuelle Quellcode unterstützt Notizen zu Loadouts und bearbeitbare MOD-Felder wie `function`, `details` und `tags`. Damit wird kein eigenes Notizfeld „Warum ich diesen MOD heruntergeladen habe“ pro MOD zugesagt. Die Wiederherstellung des Kontexts hängt von bereits vorhandenen oder von dir ergänzten Informationen ab; fehlende ursprüngliche Absichten werden nicht automatisch rekonstruiert.

<a id="see-the-product-before-installing"></a>

## Das Produkt vor der Installation ansehen

Diese Screenshots stammen aus den **acht vollständig erfundenen Demo-Datensätzen** des Repositorys. Sie enthalten keine echten MODs, Spielinhalte oder Daten fremder Websites. Sie zeigen den tatsächlichen öffentlichen Build nach dem Start, keinen Designentwurf:

![Öffentlicher Demokatalog mit Filtern](../../docs/assets/demo-browse.png)

![Detailbereich der öffentlichen Demo](../../docs/assets/demo-detail.png)

![Stichwortsuche der öffentlichen Demo](../../docs/assets/demo-search.png)

![Schmales Bildschirmlayout der öffentlichen Demo](../../docs/assets/demo-mobile.png)

Den vollständigen reproduzierbaren Rundgang findest du in [`docs/demo-walkthrough.md`](../../docs/demo-walkthrough.md).

<a id="user-supplied-screenshots-from-actual-use"></a>

### Vom Nutzer bereitgestellte Screenshots aus dem tatsächlichen Einsatz

Diese Bilder zeigen die eigene lokale Bibliothek des Nutzers, einschließlich Browsing, Filtern und Details bei einer größeren Sammlung. Sie sind weder mitgelieferte Daten noch die oben gezeigte reproduzierbare Demo mit acht Datensätzen. Eintragszahlen, Spielzahlen und Vorschaubilder geben die Umgebung des Nutzers zum Aufnahmezeitpunkt wieder, nicht die bei der Installation enthaltenen Inhalte.

![Tatsächlicher Einsatz: MOD-Bibliothek für mehrere Spiele](../../docs/assets/real-use/library-overview.png)

*Kartenansicht in der spielübergreifenden Bibliothek des Nutzers.*

![Tatsächlicher Einsatz: nach Zweck filtern](../../docs/assets/real-use/purpose-filters.png)

*Zweckbezogenes Filtern, während Karten und Filterkontext sichtbar bleiben.*

![Tatsächlicher Einsatz: MOD-Detailbereich](../../docs/assets/real-use/mod-detail-panel.png)

*Einen einzelnen Eintrag neben der aktuellen Katalogansicht prüfen.*

Die anderen drei Bilder: [Dateien und Varianten](../../docs/assets/real-use/files-and-variants.png), [KI- und Aufgabenzentrale](../../docs/assets/real-use/ai-task-center.png) und [Downloadzentrale](../../docs/assets/real-use/download-center.png).

Alle sechs Bilder mit Hinweisen zu ihren Zuständen findest du in der [Galerie aus dem tatsächlichen Einsatz](../../docs/real-use-gallery.md#english). Die Bilder der KI- und Aufgabenzentrale sowie der Downloadzentrale dokumentieren nur sichtbare Zustände in der lokalen Oberfläche des Nutzers. Sie belegen weder den Erfolg eines Auftrags oder Downloads noch, dass dieselben Funktionen im aktuellen öffentlichen Quellcode oder Release enthalten sind.

Spiel- und MOD-Namen sowie Vorschaubilder können Rechten Dritter unterliegen. Durch ihre Darstellung in diesem Repository werden sie nicht MIT-lizenziert. Die Galerie verteilt weder die zugrunde liegenden MODs noch Spielinhalte oder die Quellbibliothek und erteilt keine Erlaubnis zur Wiederverwendung fremder Inhalte.

<a id="decide-in-30-seconds-whether-it-fits"></a>

### In 30 Sekunden entscheiden, ob es passt

| Wenn du Folgendes möchtest … | Die Antwort von Local MOD Browser |
| --- | --- |
| MODs aus mehreren Spielen und Laufwerken an einem Ort durchsuchen | Mehrere lokale Quellen mit einem gemeinsamen abfragbaren Index konfigurieren |
| Dich erinnern, wozu ein heruntergeladener MOD dient | Vorhandene Zusammenfassungen, Funktionsbeschreibungen und Tags erneut ansehen; Pläne von Hand in Loadout-Notizen festhalten |
| Eine ganz bestimmte Datei aus einem MOD auswählen | Vergleich auf Dateiebene und ausdrückliche Auswahl; standardmäßig wird nicht der gesamte Satz einem Loadout hinzugefügt |
| Übersetzungen oder Katalogarbeit pausieren und fortsetzen | Segmentierte Aufgaben, Leases, Belege, Ereigniscursor und Wiederherstellung |
| KI nutzen, ohne dass der Dienst deinen privaten Bestand hochlädt | Lokales HTTP / CLI / MCP mit einem gemeinsamen Vertrag und standardmäßig nur an Loopback gebundenem Listener |
| Arbeit nach einem Umzug oder Upgrade wiederherstellen | Gekoppelte Sicherungen, Wiederherstellungsjournal, Versionsverlauf und stabile Ressourcenidentitäten |

<a id="who-is-it-for"></a>

### Für wen ist es gedacht?

- Spieler mit mehreren Spielen, MOD-Quellen oder über Jahre angesammelten Dateien.
- Ersteller und Betreuer, die wiederholt MOD-Informationen suchen, vergleichen, übersetzen und ordnen.
- Menschen, die KI-Unterstützung möchten und zugleich die Kontrolle über die Daten auf ihrem eigenen Rechner behalten wollen.
- Alle, die reproduzierbare, überprüfbare und wiederherstellbare Automatisierung dem bloßen Klicken und Hoffen vorziehen.

<a id="what-is-it-not"></a>

### Was ist es nicht?

Es ist keine MOD-Downloadseite, kein Installationsprogramm, kein Cracking-Werkzeug und kein entfernter Hostingdienst. Es entscheidet nicht, ob ein MOD sicher, kompatibel oder für deine Nutzung lizenziert ist. Es ordnet Informationen, die dir bereits gehören und zu deren Nutzung du berechtigt bist, und macht jede Änderung sichtbarer und kontrollierbarer. Es lädt keine MOD-Dateien herunter, verteilt sie nicht weiter und installiert oder führt sie nicht aus.

![Vorher und nachher: Aus verstreuten Ordnern wird ein lokaler Katalog](../../docs/assets/before-after.svg)

<a id="what-you-get"></a>

## Was du bekommst

<a id="a-mod-browser-built-for-long-term-use"></a>

### Einen MOD-Browser für die langfristige Nutzung

- Schnell nach Spiel, Stichwörtern, kombinierten Tags, Übersetzungsstatus, Autor, Datum und Dateiinformationen filtern.
- Zwischen Listen, Details und Verlauf verlässlich navigieren, ohne für den Kontext wieder in Ordner wechseln zu müssen.
- Bilder, Autorentexte, Dateilisten und Quelllinks ansehen; konkrete Dateikopien statt nur MOD-Namen vergleichen.
- Wichtige Einträge favorisieren und importierbare/exportierbare Loadouts speichern, um nach einer Neuinstallation oder einem Verzeichnisumzug weiterzuarbeiten.
- Breite oder schmale Bildschirme nutzen; komplexe Filter lassen sich einklappen, wichtige Ergebnisse bleiben hervorgehoben.

<a id="a-metadata-maintenance-workbench"></a>

### Einen Arbeitsbereich zur Metadatenpflege

- Änderungen vor `apply` mit `preview` prüfen, um versehentliche Bearbeitungen und Risiken von Stapeloperationen zu reduzieren.
- Übersetzungen nach Feld und Segment verwalten, mit Stapeln, Fortschritt, Qualitätsprüfungen, Stopp/Fortsetzen und idempotenter Wiederholung.
- Hintergrundaufträge unterstützen Leases, Verlängerung, Übergabe und Ereigniscursor, damit eine andere KI oder eine erneut geöffnete Seite weiterarbeiten kann.
- Wichtige Schreibvorgänge haben stabile Idempotenzschlüssel und verbindliche Belege. Nach einer Netzwerkunterbrechung zuerst das Ergebnis prüfen, bevor über einen erneuten Versuch entschieden wird.
- SQLite verwendet WAL und FULL-Synchronisierung sowie ein Wiederherstellungsjournal und gekoppelte Sicherungen, um die Datenintegrität zu priorisieren.

<a id="a-local-platform-ai-can-use-correctly"></a>

### Eine lokale Plattform, die KI korrekt bedienen kann

- Browser, CLI und optionales MCP teilen sich einen Vertrag; KI muss daher keine Browserklicks simulieren.
- 70 stabile Operationen decken Suche, Details, Revisionen, Favoriten, Loadouts, Übersetzungen und Auftragsverwaltung ab.
- Fünf deterministische Arbeitsabläufe führen KI durch Suchen, Prüfen, Ändern, Rücklesen und Berichten.
- Die lokale API lauscht standardmäßig auf `127.0.0.1`. Der Dienst ruft kein allgemeines KI-Modell auf und sendet Daten nicht automatisch in die Cloud.
- Bei Ausnahmen erhalten Clients nur eine Anfrage-ID. Lokale Diagnoseprotokolle werden getrennt gespeichert, damit Pfade und Stacktraces nicht an Aufrufer gelangen.

<a id="core-capabilities"></a>

## Kernfunktionen

| Szenario | Funktionen | Gelöstes Problem |
| --- | --- | --- |
| Informationen finden | Volltextsuche, Seitennavigation, kombinierte Tags, Filter für Autor/Datum/Übersetzungsstatus | „Ich erinnere mich ungefähr daran, aber nicht an den Speicherort“ |
| Details prüfen | Details, Bilder, Quelllinks, Dateilisten, Revisionsverlauf | „Was hat sich in dieser Version geändert?“ |
| Eine Auswahl treffen | Exakter Dateivergleich, Favoriten, Loadout-Import/-Export | „Ich brauche diese Kopie, nicht versehentlich den ganzen Satz“ |
| Metadaten bearbeiten | Preview/Apply, Versionierung, Feld-Positivlisten, Wiederherstellung aus dem Verlauf | „Stapelbereinigung soll trotzdem rückgängig gemacht werden können“ |
| Übersetzen | Segmentierte Aufgaben, Qualitätsprüfungen, Pause/Fortsetzen, idempotente Belege | „Ein unterbrochener langer Text soll nicht wieder von vorn beginnen“ |
| Mit KI zusammenarbeiten | HTTP, CLI, MCP, Leases, Übergabe, Ereigniscursor | „Verschiedene Assistenten sollen sicher weiterarbeiten können“ |
| Daten schützen | WAL/FULL, gekoppelte Sicherungen, Wiederherstellungsjournal, Lebenszyklussperren | „Nach einem Upgrade oder Absturz wiederherstellen“ |

<a id="privacy-and-security"></a>

## Datenschutz und Sicherheit

Local MOD Browser hat klare Grenzen:

- **Nur von dir bereitgestellte Metadaten werden indexiert.** Das Repository enthält keine MOD-Quellbibliotheken, Archive, Datenbanken, Sicherungen, Exporte oder Laufzeittokens von Nutzern. Ausgewählte, von Nutzern bereitgestellte Screenshots sind separate Dokumentation, keine Testdaten oder Inhaltsdownloads.
- **Es lädt keine MODs herunter, verteilt, installiert oder startet sie nicht.** Es ist eine Metadatenverwaltung, kein Download- oder Installationsprogramm.
- **Standardmäßig lauscht es nur lokal.** Der Dienst bindet sich an `127.0.0.1` und ist nicht als LAN- oder öffentlicher Dienst konzipiert.
- **Ein Konto bei Drittanbietern ist nicht erforderlich.** Optionales MCP ist nur ein lokaler Protokollzugang und ruft nicht automatisch ein entferntes Modell auf. Ein externer KI-Client kann abgerufene Daten an seinen Anbieter senden. Prüfe vor dem Verbinden die Clienteinstellungen und den genehmigten Umfang.
- **Du bist für die Berechtigung zur Nutzung fremder Daten verantwortlich.** Beachte die Bedingungen, API-Richtlinien und Inhaltslizenzen jeder Website und jedes Dienstes.

Lies die [Sicherheitsrichtlinie](../../SECURITY.md), den [Leitfaden für Beiträge](../../CONTRIBUTING.md) und die [Drittanbieterhinweise](../../THIRD_PARTY_NOTICES.md). Standardpfade für Laufzeit, Datenbank, Tokens, Diagnosen, Exporte und Testartefakte stehen in `.gitignore`, um versehentliche Commits zu reduzieren. Dies schützt keine bereits verfolgten Dateien, mit Zwang hinzugefügten Dateien oder Daten an anderen Orten. Prüfe vor jedem Commit die vorgemerkten Änderungen.

<a id="supported-platform"></a>

## Unterstützte Plattform

- Windows 10/11 x64.
- Festgelegte Laufzeit: CPython 3.13.15 x64 und SQLite 3.53.4.
- Die erste Einrichtung benötigt Netzwerkzugriff, um die festgelegte Laufzeit herunterzuladen und zu prüfen. Ein System-Python führt das Bootstrap-Skript aus.
- Laufzeitquellen, Hashes und Lizenzen stehen in [`runtime-lock.json`](../../runtime-lock.json).
- Linux und macOS werden derzeit nicht unterstützt. Der Kerndienst verwendet die Python-Standardbibliothek ohne zusätzliches Backend-Framework.

<a id="five-minute-quick-start"></a>

## Schnellstart in fünf Minuten

<a id="1-get-the-code-and-prepare-local-configuration"></a>

### 1. Code holen und lokale Konfiguration vorbereiten

```powershell
git clone https://github.com/son-gladyso/Local-Mod-Browser.git
cd Local-Mod-Browser
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
```

<a id="2-install-the-pinned-runtime-and-launch"></a>

### 2. Festgelegte Laufzeit installieren und starten

```powershell
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

Du kannst im Repository auch `启动MOD浏览器.cmd` doppelt anklicken. Der Launcher gibt eine lokale URL aus. Öffne sie, um den erfundenen Demokatalog und den Ablauf für eine leere Bibliothek zu erkunden. Für den ersten Start brauchst du keine echte MOD-Bibliothek.

Für einen direkten Download des öffentlichen Quellcodes verwende `Local-Mod-Browser-2.5.2-source.zip` aus dem [Release v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2). Die mitgelieferte Datei `SHA256SUMS.txt` dient zur Prüfung der Archivintegrität.

<a id="3-connect-your-own-catalog"></a>

### 3. Deinen eigenen Katalog anbinden

Bearbeite die von Git ignorierte Datei `data\sources.json`:

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

Lege in jedem `outputDir` eine `catalog-data.json` ab. Relative Pfade werden vom Verzeichnis aus aufgelöst, das `sources.json` enthält. Du kannst auch `LOCAL_MOD_BROWSER_SOURCES` auf eine andere Konfiguration setzen. Siehe [`config/sources.example.json`](../../config/sources.example.json) und [`examples/demo-game/catalog-data.json`](../../examples/demo-game/catalog-data.json).

<a id="4-check-the-service-and-local-api"></a>

### 4. Dienst und lokale API prüfen

```powershell
.\.runtime\python.exe -X utf8 ai.py doctor
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
```

Öffne `/api/docs` für den maschinenlesbaren Vertrag und `/api/health`, um Laufzeit, Datenbank und Dienststatus zu prüfen.

<a id="what-does-a-first-successful-run-look-like"></a>

## Wie sieht ein erfolgreicher erster Durchlauf aus?

Beginne mit den mitgelieferten erfundenen Datensätzen, ohne deine eigene Bibliothek zu importieren: Dienst starten → lokale URL öffnen → nach einem Beispiel suchen → Details öffnen → zur Liste zurückkehren. Dieser kleine Ablauf prüft Browsing und Suche, bevor du ein ganzes Laufwerk organisierst.

Bereite Windows 10/11 x64, ein System-Python, das das Bootstrap-Skript ausführen kann, und Netzwerkzugriff für den ersten Laufzeitdownload vor. Für die normale Nutzung sind weder KI noch MCP erforderlich. Abhängigkeiten für Entwicklertests stehen im [Leitfaden für Beiträge](../../CONTRIBUTING.md).

**Erfolg bedeutet:** Der erfundene Katalog ist sichtbar, Suche und Details sind nutzbar, und du kannst die Ergebnisse von `ai.py doctor` prüfen. Das bloße Laden einer Seite verifiziert weder deine eigene Quellenkonfiguration noch das Wiederherstellungsverhalten oder sämtliche Plattformoperationen.

<a id="common-questions"></a>

## Häufige Fragen

**Warum fehlt nach dem Download die große Bibliothek aus den Screenshots?** Dabei handelt es sich um vom Nutzer bereitgestellte Aufnahmen aus dem tatsächlichen Einsatz, nicht um verteilte Daten. Das Repository enthält acht erfundene Demo-Datensätze. Deine eigenen Quellen musst du separat konfigurieren.

**Scant und versteht es automatisch jeden MOD auf meinen Laufwerken?** Nein. Eingaben sind die Quellenkonfiguration und `catalog-data.json` in jedem `outputDir`, keine universelle Interpretation beliebiger Ordner. Prüfe Pfade und Metadaten anhand des [Konfigurationsbeispiels](../../config/sources.example.json).

**Kann es sich merken, warum ich einen MOD heruntergeladen habe?** Vorhandene Zusammenfassungen, Funktionsbeschreibungen und Tags helfen dir, seinen Zweck wiederzufinden. Du kannst Metadaten bearbeiten und Pläne von Hand in Loadout-Notizen schreiben. Es kann keine vergessene ursprüngliche Absicht aus den Dateien erschließen, und diese README verspricht kein separates Downloadgrund-Feld pro MOD.

**Warum ist die Liste leer?** Prüfe, ob `data\sources.json` gültig ist, von welchem Konfigurationsverzeichnis relative Pfade aufgelöst werden und ob jedes Zielverzeichnis `outputDir` eine `catalog-data.json` enthält. Folge dann dem [Benutzerhandbuch](../../docs/user-guide.md). Veröffentliche keine private Datenbank in einem Issue.

**Muss ich zum Browsen KI anbinden?** Nein. Browser und CLI funktionieren direkt. Optionales MCP ist eine lokale Schnittstelle, kein automatischer Schalter für ein Cloud-Modell. Ein von dir gewählter externer Client hat eigene Grenzen der Datenweitergabe.

**Belegt die Downloadzentrale aus dem tatsächlichen Einsatz, dass die öffentliche Version MODs herunterlädt?** Nein. Sie zeigt die lokale Oberfläche eines Nutzers mit leerer Downloadliste und nicht verbundenem Nexus. Für die öffentliche Version gilt weiterhin die Beschreibung, dass sie MODs weder herunterlädt noch installiert oder ausführt.

**Kann ich von anderen Geräten oder aus dem Internet darauf zugreifen?** Standardmäßig lauscht der Dienst auf `127.0.0.1`. Stelle ihn nicht als LAN- oder öffentlichen Dienst bereit. Andere Plattformen als Windows werden derzeit ebenfalls nicht unterstützt.

<a id="find-the-code-for-your-change"></a>

### Den Code für deine Änderung finden

- Browsing und Interaktion: Beginne in `static/`. Prüfe Listen, Details, Leer-/Fehlerzustände und das Verhalten auf schmalen Bildschirmen.
- Quellen und Suche: Beginne in `catalog.py` und den Konfigurationsbeispielen. Teste gültige und ungültige Eingaben mit synthetischen Katalogen.
- Plattformoperationen: Lies `contracts.py`, `platform_api.py` und die zugehörigen Tests gemeinsam, damit HTTP, CLI und MCP übereinstimmen.
- Persistenz oder Hintergrundaufträge: Lies zuerst den [Architekturleitfaden](../../docs/architecture.md). Decke Unterbrechung, Wiederholung und Wiederherstellung ab, ohne Beständigkeit gegen Geschwindigkeit einzutauschen.

Befehle und PR-Anforderungen stehen im [Leitfaden für Beiträge](../../CONTRIBUTING.md). Einstiegsaufgaben findest du unter [Roadmap und Mitwirkung](#roadmap-and-contributing).

<a id="ai-and-cli"></a>

## KI und CLI

Die CLI ist ein stabiler Einstiegspunkt für Skripte und KI, ohne simulierte Mausbedienung:

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

Empfohlener sicherer Ablauf:

1. Lies die Funktionen und Schnittstellendokumentation, um die von dieser Version unterstützten Operationen zu prüfen.
2. Suche und lies Ressourcen, bevor du `preview` übermittelst. Leite die Identität einer Datei nicht aus der Reihenfolge in einem Array ab.
3. Prüfe Ressourcen-IDs, Versionen und Unterschiede in der Vorschau und wende die Änderung anschließend mit einem stabilen `idempotencyKey` an.
4. Warte auf tatsächliche Endzustände von Hintergrundaufträgen und prüfe fachliches Rücklesen sowie verbindliche Belege. `queued` bedeutet nicht abgeschlossen.
5. Prüfe nach einer Unterbrechung Belege und Ereigniscursor, bevor du fortsetzt, übergibst oder einen erneuten Versuch startest.

Siehe [`docs/user-guide.md`](../../docs/user-guide.md), [`docs/ai-platform-guide.md`](../../docs/ai-platform-guide.md) und [`docs/architecture.md`](../../docs/architecture.md).

<a id="verification-and-quality-gates"></a>

## Überprüfung und Qualitätskriterien

Ein erfolgreicher Start reicht nicht aus, um das Projekt als abgeschlossen zu bezeichnen. Die öffentliche Version enthält reproduzierbare synthetische Abnahmeskripte:

```powershell
# Python regression
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v

# Startup, collaboration and contract
.\.runtime\python.exe -X utf8 tests\startup_acceptance.py
.\.runtime\python.exe -X utf8 tests\collaboration_acceptance.py
python -m pip install jsonschema==4.26.0
python -X utf8 tests\contract_audit.py --fixture

# Frontend syntax
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
```

Die Browserabnahme benötigt zusätzlich `npm install` und Playwright-Browser. Die Windows-CI installiert automatisch die festgelegte Laufzeit und führt Python-Regressionstests, Vertragsaudit und JavaScript-Prüfungen aus. Siehe den [Leitfaden für Beiträge](../../CONTRIBUTING.md).

<a id="project-map"></a>

## Projektübersicht

```text
Local-Mod-Browser/
├─ server.py                    lokaler HTTP-Dienst und einheitliche Fehlergrenze
├─ platform_api.py              70 Plattformoperationen und Geschäftsregeln
├─ contracts.py                 gemeinsamer HTTP-/CLI-/MCP-Vertrag und Schemata
├─ catalog.py                   Quellenkonfiguration, Indexierung und Abfrageprojektionen
├─ ai.py                        CLI für Skripte und KI
├─ mcp_adapter.py               optionaler lokaler MCP-Einstiegspunkt
├─ static/                      Browseroberfläche
├─ tests/                       Regressions-, Vertrags-, Start-, Zusammenarbeits-, Leistungs- und Dauertests
├─ tools/bootstrap_runtime.py   Installation und Prüfung der festgelegten Laufzeit
└─ docs/                        Benutzer-, KI-Plattform- und Architekturleitfäden
```

<a id="roadmap-and-contributing"></a>

## Roadmap und Mitwirkung

Die aktuelle öffentliche Version ist `v2.5.2`, der API-Vertrag ist `2.5.0`. Prioritäten sind:

- Lokale Metadatenarbeit schneller und leichter prüfbar machen, ohne die Datenerhebung auszuweiten.
- API, CLI und MCP im Verhalten konsistent halten, mit erklärbaren und behebbaren Fehlern.
- Daten durch synthetische Tests und reproduzierbare Abnahme schützen. Private Bestandslisten niemals als öffentliche Testdaten verwenden.
- Quellenadapter nur innerhalb klarer Inhaltsberechtigungen und der Bedingungen Dritter erweitern.

Die aktuelle Richtung steht in [`ROADMAP.md`](../../ROADMAP.md). Dokumentation, reproduzierbare Tests, Barrierefreiheit und kleine Verbesserungen an der Quellenkonfiguration eignen sich gut als erste Beiträge.

Issues, Dokumentationsverbesserungen und Pull Requests sind willkommen. Lies zuerst [CONTRIBUTING.md](../../CONTRIBUTING.md). Reiche keine persönlichen Pfade, Bestandslisten, Datenbanken, in Screenshots sichtbaren Tokens oder nicht autorisierten Inhalte Dritter ein. Externe Änderungen werden geprüft. Vor dem Zusammenführen in `main` sind CI, Code-Owner-Freigabe, geklärte Diskussionen, Datenschutzprüfungen und gezielte Tests erforderlich.

Wenn das Projekt ein echtes Problem löst, gib ihm einen Star, teile es mit jemandem, dessen MOD-Ordner unübersichtlich werden, oder reiche ein konkretes Issue ein. Klares, reproduzierbares Feedback hilft mehr als „sieht gut aus“ oder ein vager Funktionswunsch. Angenommene Verbesserungen bleiben im öffentlichen Verlauf überprüfbar.

<a id="start-with-one-small-improvement"></a>

### Mit einer kleinen Verbesserung beginnen

Wähle für deinen ersten Beitrag eine vorhandene Aufgabe:

- [FAQ zum ersten Start (#3)](https://github.com/son-gladyso/Local-Mod-Browser/issues/3): Ergänze Hinweise zur Laufzeitinstallation, Quellenkonfiguration und Fehlersuche bei fehlenden Katalogdateien einschließlich Prüfschritten.
- [Dokumentation und Validierung der Quellenkonfiguration (#2)](https://github.com/son-gladyso/Local-Mod-Browser/issues/2): Erkläre Felder und relative Pfade und decke Fehler mit synthetischen Konfigurationen ab.
- [Barrierefreie Leer- und Fehlerzustände (#1)](https://github.com/son-gladyso/Local-Mod-Browser/issues/1): Hilf Nutzern von Tastatur und Screenreader, den nächsten Schritt zu verstehen.

Prüfe vor der Festlegung deines Umfangs die aktuelle Diskussion und den Status des Issues. Kleine Dokumentationskorrekturen können direkt als PR eingereicht werden. Größere Funktionen, Datenmodelländerungen und Quellenadapter sollten gemäß dem Beitragsleitfaden zuerst besprochen werden. Für einen Beitrag musst du keine eigene MOD-Bibliothek bereitstellen.

<a id="license"></a>

## Lizenz

Der Projektcode verwendet die [MIT-Lizenz](../../LICENSE). Hinweise zur Laufzeit und zu optionalen Abhängigkeiten von Drittanbietern stehen in [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md). MIT gewährt keine Rechte an MODs, Spielinhalten, Websitedaten, Autorentexten oder anderen Inhalten Dritter.
