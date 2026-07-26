# Windowsサーバーへの移植手順

Mac上で動作確認済みのWeb版一式（`server.py` / `web/` / `transcribe.py` 等）をWindows PC・サーバーに移植する手順。コード自体はOS依存の処理を使っていないためそのまま動くはずだが、**Windows環境での動作は未検証**。

---

## 1. コピーするもの・しないもの

| 対象 | コピーする？ | 理由 |
|---|---|---|
| `transcribe.py` / `server.py` / `web/` / `requirements.txt` / `README.md` / `MANUAL.md` 等 | する | プロジェクト本体 |
| `.cache/huggingface/`（Whisperモデルのキャッシュ） | する（推奨） | ダウンロード済みモデルは単なるデータなのでそのまま使え、移植先での再ダウンロード（数百MB〜数GB）を避けられる |
| `.venv/` | **しない** | Pythonバイナリへの絶対パスを内部に持つため、別OS・別PCでは動かない。移植先で必ず作り直す |
| `input/` / `output/` | 任意 | 過去の音声・文字起こし結果を引き継ぎたい場合のみ。個人情報を含み得るため、必要な分だけ選んでコピーすること |
| `.git/` | 任意 | Git管理を続けるなら後述の「GitHub経由」を推奨 |

---

## 2. コピー方法

### GitHub経由（推奨・シンプル）

```powershell
git clone https://github.com/masauehr/audio_transcriber.git
```

`.cache/` `input/` `output/` は `.gitignore` 対象のため、clone しただけでは含まれない。モデルキャッシュを引き継ぎたい場合は、次項の方法で別途コピーする。

### フォルダを直接コピー（USBメモリ・ネットワーク共有など）

プロジェクトフォルダを丸ごとコピーし、**コピー後に `.venv/` フォルダだけ削除する**（前述の通り移植先では使えないため）。

---

## 3. Windows側の前提ソフトウェア

### Python

```powershell
winget install Python.Python.3.12
```

インストール後、新しいPowerShellを開いて確認する。

```powershell
python --version
```

`'python' は、内部コマンドまたは外部コマンド...` と出る場合はPATHが通っていない。インストーラーを使う場合は「Add python.exe to PATH」に必ずチェックを入れて再インストールする。

### ffmpeg

```powershell
winget install ffmpeg
```

または[公式サイト](https://ffmpeg.org/download.html)からダウンロードし、`bin`フォルダをPATHに追加する。

---

## 4. セットアップ

```powershell
cd audio_transcriber
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

以降、起動するたびに毎回 `.venv\Scripts\activate` を実行してから `python server.py` を叩く。

---

## 5. モデルキャッシュの確認

`.cache\huggingface\hub\` をコピー済みであれば、モデルの再ダウンロードは発生しない。コピーしていない場合は、Web版で該当モデルサイズを初めて使うときに自動ダウンロードされる（サイズにより数十秒〜数分）。

---

## 6. 起動・動作確認

```powershell
python server.py
```

- 自分のPCから: `http://localhost:8090`
- 同じLAN内の他端末から: `http://<このPCのIPアドレス>:8090`

IPアドレスは以下で確認する。

```powershell
ipconfig
```

「IPv4 アドレス」の欄に表示される値（例: `192.168.1.20`）を使う。

---

## 7. ファイアウォール設定

同じLAN内の他端末からアクセスさせる場合、Windows Defender ファイアウォールで受信を許可する必要がある。PowerShellを**管理者として実行**し、以下を入力する。

```powershell
New-NetFirewallRule -DisplayName "AudioTranscriberWeb" -Direction Inbound -Protocol TCP -LocalPort 8090 -Action Allow
```

GUIで行う場合は「Windows Defender ファイアウォールの詳細設定」→「受信の規則」→「新しい規則」→ポート→TCP→`8090`→許可、の順で設定する。

---

## 8. 常時稼働させたい場合（任意）

その都度手動で `python server.py` を起動する運用で問題なければ、この節は不要。

PC起動時に自動で立ち上げたい場合は、タスクスケジューラで以下のようなタスクを作成する。

- トリガー: ログオン時
- 操作: プログラムの開始
  - プログラム: `<プロジェクトフォルダの絶対パス>\.venv\Scripts\python.exe`
  - 引数: `server.py`
  - 開始（作業フォルダ）: `<プロジェクトフォルダの絶対パス>`

※ Windowsサービスとして常駐させるにはNSSM等の外部ツールが必要になるが、本ツールは「追加パッケージ導入不可」の環境を想定しているため非推奨。サービス化が必要な場合は運用担当者と要相談。

---

## 9. トラブルシューティング

| 症状 | 対処 |
|---|---|
| `python` / `pip` コマンドが見つからない | Python未インストールまたはPATH未設定。インストーラーで「Add python.exe to PATH」にチェックして再インストール |
| 文字起こし実行時にffmpeg関連のエラーが出る | ffmpeg未インストールまたはPATH未設定。`ffmpeg -version` で確認 |
| 同じLAN内の他端末からアクセスできない | ファイアウォールの受信規則（手順7）を確認。会社PCの場合、セキュリティソフトでブロックされている可能性があるため情シスに確認 |
| `Address already in use` 等でサーバーが起動しない | ポート8090が別プロセスで使用中。`server.py` 冒頭の `PORT` を別の番号に変更するか、使用中のプロセスを終了する |

---

## 10. 移植後の確認チェックリスト

- [ ] `python server.py` がエラーなく起動する
- [ ] 自分のPCから `http://localhost:8090` にアクセスできる
- [ ] 同じLAN内の別端末からアクセスできる
- [ ] 実際に音声ファイルをアップロードして文字起こしが完了する
- [ ] モデルキャッシュが想定通り動作する（コピー済みなら再ダウンロードが走らない）
