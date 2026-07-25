# 音声文字起こしツール マニュアル

音声ファイルをローカルで文字起こしするCLIツール。faster-whisper（OpenAI Whisperの高速再実装）を使用し、音声データを外部に送信せずすべてローカルで処理する。

---

## ファイルの場所

| ファイル | 説明 |
|---------|------|
| `/Users/masahiro/projects/audio_transcriber/transcribe.py` | CLI本体（実行ファイル）。Web版の共通ロジックもここから読み込む |
| `/Users/masahiro/projects/audio_transcriber/server.py` | Web版サーバー本体（Flask等は使わず標準ライブラリのみで実装） |
| `/Users/masahiro/projects/audio_transcriber/web/` | Web版のフロントエンド（index.html / app.js / style.css、Vanilla JS） |
| `/Users/masahiro/projects/audio_transcriber/requirements.txt` | 依存パッケージ（faster-whisper。Web版も追加パッケージ不要） |
| `/Users/masahiro/projects/audio_transcriber/input/` | 文字起こし対象の音声ファイル置き場（gitignore対象）。Web版のアップロードもここに保存 |
| `/Users/masahiro/projects/audio_transcriber/output/` | 文字起こし結果テキスト出力先（gitignore対象） |
| `/Users/masahiro/projects/audio_transcriber/.cache/huggingface/` | Whisperモデルのキャッシュ（gitignore対象）。プロジェクト内に固定しているため、フォルダごとコピーすればモデルも一緒に移植できる |

GitHub: https://github.com/masauehr/audio_transcriber （プライベート。`input/`・`output/`は音声データ・文字起こし結果を含むためコミット対象外）

---

## セットアップ

### Mac / Linux

```bash
cd /Users/masahiro/projects/audio_transcriber
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python標準ライブラリの `venv` を使う。Homebrew版Python等、システムPythonへの直接 `pip install` がPEP 668によりブロックされる環境があり、venv作成が事実上必須。以後、実行するたびに毎回 `source .venv/bin/activate` してから `python transcribe.py ...` / `python server.py` を叩く。

対応フォーマット（m4a, mp3, wav, mp4等）の変換にffmpegを使用するため、未インストールの場合は `brew install ffmpeg` が必要。

### Windows

`transcribe.py`・`server.py`はOS依存の処理を使っていないため、コードはそのままWindowsでも動く（未検証）。

```powershell
cd audio_transcriber
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Mac/Linuxとの違いは以下の1点のみ。

| 項目 | Mac / Linux | Windows |
|---|---|---|
| ffmpegのインストール | `brew install ffmpeg` | [公式サイト](https://ffmpeg.org/download.html)からダウンロードしてPATHに追加、または`winget install ffmpeg` |

### 別PCへの移植について

`.venv/` はPythonバイナリへの絶対パスを内部に持つため、**フォルダごとコピーしても別PCでは動かない**。移植する際は `.venv/` を除いてプロジェクトフォルダをコピーし、移植先で改めて上記セットアップ（`python -m venv .venv` から）をやり直す。一方 `.cache/huggingface/`（ダウンロード済みのWhisperモデル）は単なるデータファイルなのでそのままコピーしてよく、移植先での再ダウンロードを避けられる。

モデルキャッシュの保存先はOSによらずプロジェクト内 `.cache/huggingface/` に統一されている（詳細は後述の「モデルの保存先・削除方法」を参照）。

---

## 実行手順

```bash
cd /Users/masahiro/projects/audio_transcriber
python transcribe.py input/sample.m4a
```

実行後、2種類のテキストファイルが `output/` に保存される。出力先を明示指定しない場合、ファイル名に**モデル名と実行日時**を含めるため、同じ音声ファイルを複数回・異なるモデルで実行しても過去の結果が上書きされない。

| ファイル | 内容 |
|---|---|
| `output/sample_small_20260722_143000.txt` | `[HH:MM:SS - HH:MM:SS] テキスト` 形式の時刻タグ付き |
| `output/sample_small_20260722_143000_formatted.txt` | 時刻タグを除き、句点（。）ごとに改行した整形済みテキスト |

`--output` で出力先を明示指定した場合は、指定したファイル名がそのまま使われる（モデル名・実行日時は付与されない）。この場合は同じパスを指定して再実行すると上書きされるので注意。指定したファイル名と同じ場所に `_formatted` を付けたファイルが追加で生成される（例: `--output output/result.txt` なら `output/result.txt` と `output/result_formatted.txt`）。

```bash
# オプション例の一覧を表示
python transcribe.py ?
```

### オプション

| オプション | 説明 | デフォルト |
|---|---|---|
| `--model` | Whisperモデルサイズ（下記「モデルの選び方」参照） | `small` |
| `--language` | 音声の言語コード（例: `ja`） | 自動検出 |
| `--output` | 出力先テキストファイルパス | `output/<入力ファイル名>.txt` |

```bash
python transcribe.py input/meeting.m4a --model medium --language ja
```

---

## Web版（ブラウザで利用）

組織内LANで複数人が使えるように、ブラウザからアップロード・ダウンロードできるWeb版を用意している。Flask等の外部Webフレームワークは使わず、Pythonの標準ライブラリのみで動作する。

```bash
cd /Users/masahiro/projects/audio_transcriber
python server.py
```

起動後、コンソールに表示されるアドレスにブラウザでアクセスする。

- 自分のPCから: `http://localhost:8090`
- 同じLAN内の他の端末から: `http://<このPCのIPアドレス>:8090`

ブラウザ上で音声ファイルを選択し、モデルサイズ・言語を選んで送信すると、文字起こしが開始される。処理には数十秒〜数十分かかるため、進捗（プログレスバー）が表示される。選択したモデルサイズが初回利用（未ダウンロード）の場合は「モデルをダウンロード中...」というオレンジ色のインジケータが表示され、文字起こし処理（青色の進捗バー）とは見た目で区別できる。完了後は整形済み・時刻タグ付きをタブで切り替えてブラウザ内に表示でき、両方のダウンロードも可能。

### 認証・アクセス範囲について

**認証機能はない。** 同じLAN上の端末であれば誰でもアクセス・音声ファイルをアップロードできる想定（組織内LAN限定・少人数利用のため、シンプルさを優先した設計）。社外からアクセスできるネットワークでは使わないこと。

### データの自動削除

アップロードされた音声ファイル（`input/`）と文字起こし結果（`output/`）は、いずれも**30日経過すると自動削除**される（サーバー起動時にチェックされる）。個人情報を含み得るデータを長期間保持しない方針のため。30日以内でも手動で削除して問題ない。

### 既知の制約

- サーバーを再起動すると、実行中・完了済みのジョブ状態（進捗・ダウンロードリンク）はリセットされる（結果ファイル自体は`output/`に残るので、必要なら手動で取り出せる）
- 複数のモデルサイズを切り替えて使うと、読み込んだモデルがメモリに乗ったままになる（サーバーを再起動すればリセットされる）

---

## モデルの選び方

モデルが大きいほど精度は上がるが、ダウンロード容量とCPUでの処理時間も増える。日本語の会議・スピーチ音声では `small` は誤認識（同音異義語の取り違え、固有名詞の誤変換など）がやや多く、`medium` 以上で実用的な精度になる体感。

| モデル | 精度目安 | 速度（CPU） | ダウンロード容量目安 | 用途 |
|---|---|---|---|---|
| `tiny` | 低 | 非常に速い | 約75MB | 動作確認・下書き |
| `base` | 低〜中 | 速い | 約145MB | 雑音の少ない短い音声 |
| `small`（デフォルト） | 中 | 標準 | 約480MB（実測464MB） | 手早く内容を把握したい場合 |
| `medium` | 高 | やや遅い | 約1.5GB（実測1.4GB） | 通常の会議・インタビュー。誤字がsmallよりかなり減る |
| `large-v3-turbo` | 高〜最高 | `medium`よりやや遅い程度 | 約1.6GB（実測1.5GB） | 精度と速度のバランス重視。実用上の第一候補 |
| `large-v3` | 最高 | かなり遅い（長時間音声はCPUで数十分〜） | 約3.1GB（実測2.9GB） | 専門用語・多言語混在音声など精度最優先 |

迷ったら `medium` → 精度が足りなければ `large-v3-turbo` の順で試すのが実用的。

---

## モデルの保存先・削除方法

ダウンロードしたモデルは、プロジェクト内の `.cache/huggingface/hub/` 以下に保存され、2回目以降は再ダウンロードなしで使われる（`transcribe.py`冒頭で`HF_HOME`をプロジェクト内に固定しているため。移植性のため、あえてホームディレクトリの`~/.cache/`ではなくプロジェクトフォルダ内に置いている。プロジェクトフォルダごとコピーすれば、ダウンロード済みモデルも一緒に別のPCへ持ち出せる）。

```bash
# Mac / Linux / Windows共通: キャッシュ済みモデルと容量の確認
du -sh .cache/huggingface/hub/models--*whisper*

# 特定モデルの削除（例: smallを削除）
rm -rf .cache/huggingface/hub/models--Systran--faster-whisper-small
```

ディスク容量が気になる場合、使わないモデルはこの方法で個別に削除してよい（次回そのモデルを指定すると自動で再ダウンロードされる）。

※ 本ツールを以前のバージョンから使っていて `~/.cache/huggingface/hub/` にモデルが既にダウンロード済みの場合、自動移行はされない。初回実行時に再ダウンロードされるか、手動で `.cache/huggingface/` 以下にコピーすれば再ダウンロードを避けられる。

---

## 個人情報の取り扱い

- `input/`（音声ファイル）・`output/`（文字起こし結果）はいずれも個人情報を含み得るため `.gitignore` で除外し、リポジトリにコミットしない
- 文字起こし処理はfaster-whisperによる完全ローカル処理で、音声データは外部（クラウドAPI等）に送信されない
- Web版は認証なしで組織内LANに公開されるため、社外からアクセスできるネットワーク上では稼働させないこと
- Web版でアップロードされた音声・文字起こし結果は30日経過後に自動削除される（前述「Web版」セクション参照）

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-07-22 | 新規作成。faster-whisperによるローカルCLIツールとして構築 |
| 2026-07-22 | モデルの選び方・保存先・削除方法を追記。`transcribe.py ?` でオプション例を表示する機能を追加 |
| 2026-07-22 | Windowsでのセットアップ手順・モデルキャッシュの保存先/削除方法を追記（未検証） |
| 2026-07-22 | 実行のたびに時刻タグ付き（`<name>.txt`）と時刻タグなし整形済み（`<name>_formatted.txt`）の2ファイルを自動生成するよう変更 |
| 2026-07-22 | 出力先未指定時、ファイル名にモデル名・実行日時を含めて上書きを防止するよう変更 |
| 2026-07-25 | ブラウザから利用できるWeb版（`server.py`）を追加。Flask等は使わず標準ライブラリのみで実装。音声アップロード→進捗表示→結果ダウンロードに対応。認証なし・組織内LAN限定・30日で自動削除。モデルキャッシュを`~/.cache/`からプロジェクト内`.cache/`に変更し、フォルダごとの移植を容易にした |
| 2026-07-25 | Mac/LinuxのセットアップにPython標準の`venv`使用を明記（Homebrew版Python等でシステムPythonへの直接pip installがブロックされるため）。`.venv/`はPythonバイナリへの絶対パス依存のため移植不可（`.cache/`のモデルキャッシュのみ移植可能）である旨を追記 |
