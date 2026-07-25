# 音声文字起こしツール

詳しくは [MANUAL.md](MANUAL.md) を参照。

音声ファイルをローカルで文字起こしするツール。[faster-whisper](https://github.com/SYSTRAN/faster-whisper)（OpenAI Whisperの高速再実装）を使用し、音声データを外部に送信せず、すべてローカルで処理する。CLI（`transcribe.py`）とWeb版（`server.py`、ブラウザからアップロード・ダウンロード）の両方に対応。

## 特徴

- **完全ローカル処理**: 音声データはネットワークに送信されない（個人情報を含む音声でも安心して使える）
- **日本語対応**: 言語自動検出、または `--language ja` で明示指定可能
- **2種類のテキストを同時出力**: `[HH:MM:SS - HH:MM:SS] テキスト` 形式の**時刻タグ付き**と、時刻タグを除いて句点ごとに改行した**整形済み**（`_formatted.txt`）の両方を `output/` に生成
- **上書き防止**: 出力先を明示指定しない場合、ファイル名に実行日時とモデル名を含めるため、同じ音声を複数回・別モデルで実行しても過去の結果が消えない
- **Web版あり**: Flask等は使わず標準ライブラリのみで実装。組織内LANで複数人がブラウザから利用できる（認証なし、社内LAN限定を想定）
- **移植しやすい**: Whisperモデルのキャッシュはプロジェクト内 `.cache/` に保存されるため、フォルダごとコピーすればモデルも一緒に別PCへ移せる

## セットアップ

### Mac / Linux

```bash
cd audio_transcriber
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python標準ライブラリの`venv`を使う（Homebrew版Python等、システムPythonへの直接`pip install`がブロックされる環境があるため）。以後起動するときは毎回 `source .venv/bin/activate` してから `python transcribe.py ...` / `python server.py` を実行する。

初回実行時にWhisperモデル（`small` はおよそ500MB）が自動ダウンロードされ、プロジェクト内 `.cache/huggingface/` にキャッシュされる（移植性のため、ホームディレクトリではなくプロジェクト内に固定している）。

### Windows

```powershell
cd audio_transcriber
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

コード自体はOS依存の処理を使っていないため、Windowsでも同じ`transcribe.py`・`server.py`がそのまま動く。ただし以下の1点はMacと異なる。

- **ffmpeg**: `brew install ffmpeg` の代わりに、[公式サイト](https://ffmpeg.org/download.html)からダウンロードしてPATHに追加するか、`winget install ffmpeg` を実行する

モデルキャッシュの保存先はOSによらずプロジェクト内 `.cache/huggingface/` に統一されている。

※ Windows環境での動作は未検証。ffmpegのPATH設定でつまずく可能性がある。

### 別PCへの移植について

`.venv/` はPythonバイナリへの絶対パスを含むため、フォルダごとコピーしても別PCでは動かない。移植先では **`.venv/` を除いて**プロジェクトフォルダをコピーし、移植先で改めて上記のセットアップ手順（`python -m venv .venv` から）をやり直すこと。一方 `.cache/huggingface/`（ダウンロード済みモデル）は単なるデータなのでそのままコピーしてよく、移植先での再ダウンロードを避けられる。

## 使い方

```bash
# input/ に音声ファイルを置いて実行
# → output/sample_small_<実行日時>.txt（時刻タグ付き）と
#   output/sample_small_<実行日時>_formatted.txt（整形済み）を生成
python transcribe.py input/sample.m4a

# モデルサイズ・言語を指定（ファイル名にもモデル名が入るので結果を比較しやすい）
python transcribe.py input/sample.m4a --model medium --language ja

# 出力先を指定（この場合はファイル名固定・上書きされるので注意）
python transcribe.py input/sample.m4a --output output/result.txt

# オプション例の一覧を表示
python transcribe.py ?
```

## Web版（ブラウザで利用）

組織内LANで複数人が使えるように、ブラウザからアップロード・ダウンロードできるWeb版を用意している。認証機能はなく、社内LAN限定・少人数利用を想定している。

```bash
python server.py
# → http://localhost:8090 （同じLAN内の他端末からは http://<このPCのIPアドレス>:8090）
```

音声ファイルをアップロードすると進捗が表示され、完了後に時刻タグ付き・整形済みの両方をダウンロードできる。アップロードされた音声・結果は30日で自動削除される。詳細は [MANUAL.md](MANUAL.md) の「Web版」セクションを参照。

### 対応フォーマット

m4a, mp3, wav, mp4 など、ffmpegが対応する主要な音声・動画フォーマット。ffmpeg未インストールの場合は `brew install ffmpeg` が必要。

### モデルサイズ

日本語の会議・スピーチ音声では `small` はやや誤認識が多く、`medium` 以上で実用精度になる体感。詳しい比較・保存先・削除方法は [MANUAL.md](MANUAL.md) を参照。

| モデル | 精度 | 速度（CPU） | 用途 |
|---|---|---|---|
| `tiny` / `base` | 低 | 速い | 下書き・雑音の少ない音声 |
| `small`（デフォルト） | 中 | 標準 | 手早く内容を把握したい場合 |
| `medium` | 高 | やや遅い | 通常の会議・インタビュー |
| `large-v3-turbo` | 高〜最高 | `medium`よりやや遅い程度 | 精度と速度のバランス重視。実用上の第一候補 |
| `large-v3` | 最高 | かなり遅い | 専門用語・多言語混在音声 |

## 注意事項

- `input/` `output/` 配下のファイルは `.gitignore` で除外している（音声データ・文字起こし結果には個人情報が含まれ得るため、リポジトリにはコミットしない）
- 長時間の音声（1時間超）は `medium` 以上のモデルだとCPUでかなり時間がかかる。まず `small` で試すことを推奨
