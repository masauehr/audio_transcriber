const POLL_INTERVAL_MS = 3000;

const form = document.getElementById("upload-form");
const submitBtn = document.getElementById("submit-btn");
const statusArea = document.getElementById("status-area");
const statusText = document.getElementById("status-text");
const progressFill = document.getElementById("progress-fill");
const resultArea = document.getElementById("result-area");
const errorArea = document.getElementById("error-area");
const errorText = document.getElementById("error-text");

const STATUS_LABELS = {
  pending: "順番待ち中...",
  downloading_model: "モデルをダウンロード中...（初回のみ。サイズによっては数分かかります）",
  running: "文字起こし中...",
  done: "完了しました",
  error: "エラーが発生しました",
};

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function resetPanels() {
  statusArea.hidden = false;
  resultArea.hidden = true;
  errorArea.hidden = true;
  progressFill.style.width = "0%";
}

function showError(message) {
  statusArea.hidden = true;
  resultArea.hidden = true;
  errorArea.hidden = false;
  errorText.textContent = message;
}

const resultText = document.getElementById("result-text");
const tabButtons = document.querySelectorAll(".tab-btn");
let currentJobId = null;

async function loadResultText(jobId, type) {
  resultText.textContent = "読み込み中...";
  try {
    const res = await fetch(`/api/jobs/${jobId}/download?type=${type}`);
    resultText.textContent = res.ok ? await res.text() : "結果の取得に失敗しました。";
  } catch (e) {
    resultText.textContent = "結果の取得に失敗しました。";
  }
}

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    loadResultText(currentJobId, btn.dataset.type);
  });
});

function showResult(jobId) {
  statusArea.hidden = true;
  errorArea.hidden = true;
  resultArea.hidden = false;
  currentJobId = jobId;
  document.getElementById("download-timestamped").href =
    `/api/jobs/${jobId}/download?type=timestamped`;
  document.getElementById("download-formatted").href =
    `/api/jobs/${jobId}/download?type=formatted`;

  tabButtons.forEach((b) => b.classList.remove("active"));
  document.querySelector('.tab-btn[data-type="formatted"]').classList.add("active");
  loadResultText(jobId, "formatted");
}

function pollStatus(jobId) {
  const timer = setInterval(async () => {
    let res;
    try {
      res = await fetch(`/api/jobs/${jobId}`);
    } catch (e) {
      clearInterval(timer);
      showError("サーバーとの通信に失敗しました。");
      submitBtn.disabled = false;
      return;
    }
    const job = await res.json();
    if (!res.ok) {
      clearInterval(timer);
      showError(job.error || "ジョブの状態取得に失敗しました。");
      submitBtn.disabled = false;
      return;
    }

    statusText.textContent = STATUS_LABELS[job.status] || job.status;
    if (job.status === "downloading_model") {
      progressFill.classList.add("indeterminate");
    } else {
      progressFill.classList.remove("indeterminate");
      if (typeof job.progress === "number") {
        progressFill.style.width = `${Math.round(job.progress * 100)}%`;
      }
    }

    if (job.status === "done") {
      clearInterval(timer);
      showResult(jobId);
      submitBtn.disabled = false;
    } else if (job.status === "error") {
      clearInterval(timer);
      showError(job.error || "文字起こし中にエラーが発生しました。");
      submitBtn.disabled = false;
    }
  }, POLL_INTERVAL_MS);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("audio-file").files[0];
  if (!file) return;

  submitBtn.disabled = true;
  resetPanels();
  statusText.textContent = "アップロード中...";

  try {
    const audio_base64 = await fileToBase64(file);
    const res = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: file.name,
        model: document.getElementById("model-size").value,
        language: document.getElementById("language").value,
        audio_base64,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      showError(data.error || "送信に失敗しました。");
      submitBtn.disabled = false;
      return;
    }
    statusText.textContent = STATUS_LABELS.pending;
    pollStatus(data.job_id);
  } catch (err) {
    showError("送信中にエラーが発生しました: " + err.message);
    submitBtn.disabled = false;
  }
});
