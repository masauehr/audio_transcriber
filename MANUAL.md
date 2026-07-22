# 音声文字起こしツール マニュアル

音声ファイルをローカルで文字起こしするCLIツール。faster-whisper（OpenAI Whisperの高速再実装）を使用し、音声データを外部に送信せずすべてローカルで処理する。

---

## ファイルの場所

| ファイル | 説明 |
|---------|------|
| `/Users/masahiro/projects/audio_transcriber/transcribe.py` | メインスクリプト（実行ファイル） |
| `/Users/masahiro/projects/audio_transcriber/requirements.txt` | 依存パッケージ（faster-whisper） |
| `/Users/masahiro/projects/audio_transcriber/input/` | 文字起こし対象の音声ファイル置き場（gitignore対象） |
| `/Users/masahiro/projects/audio_transcriber/output/` | 文字起こし結果テキスト出力先（gitignore対象） |

GitHub: https://github.com/masauehr/audio_transcriber （プライベート。`input/`・`output/`は音声データ・文字起こし結果を含むためコミット対象外）

---

## セットアップ

### Mac / Linux

```bash
cd /Users/masahiro/projects/audio_transcriber
pip install -r requirements.txt
```

対応フォーマット（m4a, mp3, wav, mp4等）の変換にffmpegを使用するため、未インストールの場合は `brew install ffmpeg` が必要。

### Windows

`transcribe.py`はOS依存の処理を使っていないため、コードはそのままWindowsでも動く（未検証）。

```powershell
cd audio_transcriber
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Mac/Linuxとの違いは以下の2点。

| 項目 | Mac / Linux | Windows |
|---|---|---|
| ffmpegのインストール | `brew install ffmpeg` | [公式サイト](https://ffmpeg.org/download.html)からダウンロードしてPATHに追加、または`winget install ffmpeg` |
| モデルキャッシュの保存先 | `~/.cache/huggingface/hub/` | `%USERPROFILE%\.cache\huggingface\hub\`（例: `C:\Users\<ユーザー名>\.cache\huggingface\hub\`） |

---

## 実行手順

```bash
cd /Users/masahiro/projects/audio_transcriber
python transcribe.py input/sample.m4a
```

実行後、`output/sample.txt` にタイムスタンプ付きの文字起こし結果が保存される。

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

ダウンロードしたモデルは `~/.cache/huggingface/hub/` 以下（Windowsは `%USERPROFILE%\.cache\huggingface\hub\`）に保存され、2回目以降は再ダウンロードなしで使われる。

```bash
# Mac / Linux: キャッシュ済みモデルと容量の確認
du -sh ~/.cache/huggingface/hub/models--*whisper*

# Mac / Linux: 特定モデルの削除（例: smallを削除）
rm -rf ~/.cache/huggingface/hub/models--Systran--faster-whisper-small
```

```powershell
# Windows: 特定モデルの削除（例: smallを削除）
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-small"
```

ディスク容量が気になる場合、使わないモデルはこの方法で個別に削除してよい（次回そのモデルを指定すると自動で再ダウンロードされる）。

---

## 個人情報の取り扱い

- `input/`（音声ファイル）・`output/`（文字起こし結果）はいずれも個人情報を含み得るため `.gitignore` で除外し、リポジトリにコミットしない
- 文字起こし処理はfaster-whisperによる完全ローカル処理で、音声データは外部（クラウドAPI等）に送信されない

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-07-22 | 新規作成。faster-whisperによるローカルCLIツールとして構築 |
| 2026-07-22 | モデルの選び方・保存先・削除方法を追記。`transcribe.py ?` でオプション例を表示する機能を追加 |
| 2026-07-22 | Windowsでのセットアップ手順・モデルキャッシュの保存先/削除方法を追記（未検証） |
