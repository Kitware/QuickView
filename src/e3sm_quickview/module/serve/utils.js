class QueryFilter {
  constructor() {
    this.exacts = [];
    this.regulars = [];
    this.startsWith = [];
    this.endsWith = [];
    this.currentQuery = null;
  }

  updateQuery(query) {
    if (this.currentQuery === query) {
      return;
    }
    this.currentQuery = query;

    const pendingExact = [];
    const exacts = [];
    const regulars = [];
    const startsWith = [];
    const endsWith = [];
    const tokens = query.split(" ");
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i];

      // Handle pending exact
      if (pendingExact.length) {
        pendingExact.push(token);

        if (token.endsWith('"')) {
          exacts.push(pendingExact.join(" ").replaceAll('"', ""));
          pendingExact.length = 0;
        }
        continue;
      }

      // Handle exact token
      if (token.startsWith('"')) {
        if (token.endsWith('"')) {
          exacts.push(token.replaceAll('"', ""));
        } else {
          pendingExact.push(token);
        }
        continue;
      }

      // Handle startsWith
      if (token.startsWith("*")) {
        endsWith.push(token.replaceAll("*", "").toLowerCase());
        continue;
      }

      // Handle endsWith
      if (token.endsWith("*")) {
        startsWith.push(token.replaceAll("*", "").toLowerCase());
        continue;
      }

      regulars.push(token.toLowerCase());
    }
    // Clear pending
    if (pendingExact.length) {
      exacts.push(pendingExact.join(" ").replaceAll('"', ""));
    }

    this.exacts = exacts;
    this.regulars = regulars;
    this.startsWith = startsWith;
    this.endsWith = endsWith;
  }

  keepItem({ name, type }) {
    // Filter exact first
    for (let i = 0; i < this.exacts.length; i++) {
      const exact = this.exacts[i];
      if (name !== exact && type !== exact) {
        return false;
      }
    }

    const nameLower = name.toLowerCase();
    const typeLower = type.toLowerCase();

    // startsWith
    for (let i = 0; i < this.startsWith.length; i++) {
      if (!nameLower.startsWith(this.startsWith[i])) {
        return false;
      }
    }

    // endsWith
    for (let i = 0; i < this.endsWith.length; i++) {
      if (!nameLower.endsWith(this.endsWith[i])) {
        return false;
      }
    }

    if (this.regulars.length) {
      return this.regulars.every(
        (v) => nameLower.includes(v) || typeLower.includes(v),
      );
    }
    return true;
  }
}

QUERY_FILTER = new QueryFilter();

// ---------------------------------------------------------------------------
// Panel capture helpers
// ---------------------------------------------------------------------------

function _findPanelCard(variableName) {
  // Look for the VCard by its datapanel attribute (set in Python).
  const card = document.querySelector(`.v-card[datapanel="${variableName}"]`);
  if (card) return card;

  // Fallback: match by title text
  const cards = document.querySelectorAll(".v-card");
  for (const c of cards) {
    const sub = c.querySelector(".text-subtitle-2");
    if (sub && sub.textContent.trim() === variableName) {
      return c;
    }
  }
  return null;
}

function _downloadDataURL(dataURL, filename) {
  const a = document.createElement("a");
  a.href = dataURL;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// Shared screen-capture stream.
// Opened once (on user gesture), reused across frames, closed after use.
window.__captureStream = null;
window.__captureVideo = null;
window.__captureFrames = [];

async function _ensureCaptureStream() {
  if (window.__captureStream && window.__captureVideo) {
    return window.__captureVideo;
  }
  _hideCaptureArtifacts();
  const stream = await navigator.mediaDevices.getDisplayMedia({
    video: { displaySurface: "browser", cursor: "never" },
    preferCurrentTab: true,
  });
  window.__captureStream = stream;
  const video = document.createElement("video");
  video.srcObject = stream;
  video.autoplay = true;
  await new Promise((resolve) => {
    video.onloadedmetadata = () => {
      video.play();
      requestAnimationFrame(() => requestAnimationFrame(resolve));
    };
  });
  window.__captureVideo = video;
  return video;
}

function _stopCaptureStream() {
  if (window.__captureStream) {
    for (const track of window.__captureStream.getTracks()) track.stop();
  }
  window.__captureStream = null;
  window.__captureVideo = null;
  _restoreCaptureArtifacts();
}

function _hideCaptureArtifacts() {
  // Hide cursor so it doesn't appear in screen capture
  document.documentElement.style.cursor = "none";
  document.body.style.cursor = "none";
  // Hide tooltips
  document
    .querySelectorAll(".v-tooltip .v-overlay__content")
    .forEach((el) => (el.style.display = "none"));
  if (document.activeElement) document.activeElement.blur();
}

function _restoreCaptureArtifacts() {
  document.documentElement.style.cursor = "";
  document.body.style.cursor = "";
  document
    .querySelectorAll(".v-tooltip .v-overlay__content")
    .forEach((el) => (el.style.display = ""));
}

function _cropCardFromVideo(card, video) {
  const vw = video.videoWidth;
  const vh = video.videoHeight;
  const scaleX = vw / window.innerWidth;
  const scaleY = vh / window.innerHeight;
  const rect = card.getBoundingClientRect();
  const sx = Math.round(rect.left * scaleX);
  const sy = Math.round(rect.top * scaleY);
  const sw = Math.round(rect.width * scaleX);
  const sh = Math.round(rect.height * scaleY);

  const canvas = document.createElement("canvas");
  canvas.width = sw;
  canvas.height = sh;
  canvas.getContext("2d").drawImage(video, sx, sy, sw, sh, 0, 0, sw, sh);
  return canvas;
}

async function capturePanel(variableName, timeIdx, midpointIdx, interfaceIdx) {
  const card = _findPanelCard(variableName);
  if (!card) {
    console.warn(`[capture] Panel for "${variableName}" not found`);
    return;
  }

  _hideCaptureArtifacts();
  await new Promise((r) => setTimeout(r, 300));

  try {
    const video = await _ensureCaptureStream();
    const canvas = _cropCardFromVideo(card, video);
    const dataURL = canvas.toDataURL("image/png");

    let filename = variableName;
    if (timeIdx != null) filename += `_t${timeIdx}`;
    if (midpointIdx != null) filename += `_k${midpointIdx}`;
    if (interfaceIdx != null) filename += `_k${interfaceIdx}`;
    _downloadDataURL(dataURL, `${filename}.png`);
  } catch (err) {
    console.error("[capture] Screen capture failed:", err);
  } finally {
    _restoreCaptureArtifacts();
    _stopCaptureStream();
  }
}

function captureCollectFrame(variableName, frameIndex) {
  const card = _findPanelCard(variableName);
  const video = window.__captureVideo;
  if (!card || !video) {
    console.warn(
      `[capture] frame ${frameIndex}: card=${!!card} video=${!!video}`,
    );
    return;
  }

  const canvas = _cropCardFromVideo(card, video);
  const dataURL = canvas.toDataURL("image/png");
  // Decode data URL to Uint8Array eagerly so download can be synchronous
  const binary = atob(dataURL.split(",")[1]);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const pad = String(frameIndex).padStart(5, "0");
  window.__captureFrames.push({
    name: `${variableName}_${pad}.png`,
    data: bytes,
  });
  console.log(`[capture] collected frame ${frameIndex}, ${bytes.length} bytes`);
}

// CRC-32 lookup table
const _crc32Table = (() => {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[i] = c;
  }
  return table;
})();

function _crc32(data) {
  let crc = 0xffffffff;
  for (let i = 0; i < data.length; i++) {
    crc = _crc32Table[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function _dosDateTime() {
  const d = new Date();
  const time =
    (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1);
  const date =
    ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
  return { time, date };
}

function _buildZipBlob(entries) {
  // entries: [{name: string, data: Uint8Array}, ...]
  const parts = [];
  const centralDir = [];
  let offset = 0;
  const { time: dosTime, date: dosDate } = _dosDateTime();

  for (const file of entries) {
    const nameBytes = new TextEncoder().encode(file.name);
    const data = file.data;
    const crc = _crc32(data);

    const localHeader = new Uint8Array(30 + nameBytes.length);
    const lv = new DataView(localHeader.buffer);
    lv.setUint32(0, 0x04034b50, true);
    lv.setUint16(4, 20, true);
    lv.setUint16(6, 0, true);
    lv.setUint16(8, 0, true);
    lv.setUint16(10, dosTime, true);
    lv.setUint16(12, dosDate, true);
    lv.setUint32(14, crc, true);
    lv.setUint32(18, data.length, true);
    lv.setUint32(22, data.length, true);
    lv.setUint16(26, nameBytes.length, true);
    lv.setUint16(28, 0, true);
    localHeader.set(nameBytes, 30);

    const cdEntry = new Uint8Array(46 + nameBytes.length);
    const cv = new DataView(cdEntry.buffer);
    cv.setUint32(0, 0x02014b50, true);
    cv.setUint16(4, 20, true);
    cv.setUint16(6, 20, true);
    cv.setUint16(8, 0, true);
    cv.setUint16(10, dosTime, true);
    cv.setUint16(12, dosDate, true);
    cv.setUint16(14, 0, true);
    cv.setUint32(16, crc, true);
    cv.setUint32(20, data.length, true);
    cv.setUint32(24, data.length, true);
    cv.setUint16(28, nameBytes.length, true);
    cv.setUint16(30, 0, true);
    cv.setUint16(32, 0, true);
    cv.setUint16(34, 0, true);
    cv.setUint16(36, 0, true);
    cv.setUint32(38, 0, true);
    cv.setUint32(42, offset, true);
    cdEntry.set(nameBytes, 46);

    parts.push(localHeader, data);
    centralDir.push(cdEntry);
    offset += localHeader.length + data.length;
  }

  let cdSize = 0;
  for (const e of centralDir) cdSize += e.length;
  const eocd = new Uint8Array(22);
  const ev = new DataView(eocd.buffer);
  ev.setUint32(0, 0x06054b50, true);
  ev.setUint16(4, 0, true);
  ev.setUint16(6, 0, true);
  ev.setUint16(8, entries.length, true);
  ev.setUint16(10, entries.length, true);
  ev.setUint32(12, cdSize, true);
  ev.setUint32(16, offset, true);
  ev.setUint16(20, 0, true);

  return new Blob([...parts, ...centralDir, eocd], { type: "application/zip" });
}

function _renderVideoFromFrames(frames, fps) {
  return new Promise((resolve, reject) => {
    if (!frames.length) return reject("No frames");

    const firstImg = new Image();
    const firstBlob = new Blob([frames[0].data], { type: "image/png" });
    firstImg.onload = () => {
      const w = firstImg.naturalWidth;
      const h = firstImg.naturalHeight;
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");

      const stream = canvas.captureStream(0);
      const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
        ? "video/webm;codecs=vp9"
        : "video/webm";
      const recorder = new MediaRecorder(stream, {
        mimeType,
        videoBitsPerSecond: 8_000_000,
      });
      const chunks = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size) chunks.push(e.data);
      };
      recorder.onstop = () => {
        const videoBlob = new Blob(chunks, { type: mimeType });
        videoBlob.arrayBuffer().then((ab) => {
          resolve({ data: new Uint8Array(ab), ext: "webm" });
        });
      };
      recorder.onerror = reject;
      recorder.start();

      let idx = 0;
      const drawNext = () => {
        if (idx >= frames.length) {
          recorder.stop();
          return;
        }
        const img = new Image();
        const blob = new Blob([frames[idx].data], { type: "image/png" });
        img.onload = () => {
          ctx.clearRect(0, 0, w, h);
          ctx.drawImage(img, 0, 0, w, h);
          URL.revokeObjectURL(img.src);
          const track = stream.getVideoTracks()[0];
          if (track.requestFrame) track.requestFrame();
          idx++;
          setTimeout(drawNext, 1000 / fps);
        };
        img.src = URL.createObjectURL(blob);
      };
      drawNext();
    };
    firstImg.src = URL.createObjectURL(firstBlob);
  });
}

function captureDownloadZip(variableName) {
  const frames = window.__captureFrames;
  if (!frames.length) {
    console.warn("[capture] No frames collected");
    return;
  }
  console.log(`[capture] building ZIP with ${frames.length} frames + video`);

  const fps = 5;
  _renderVideoFromFrames(frames, fps)
    .then((video) => {
      // Add video to the entries alongside the PNGs
      const entries = frames.map((f) => ({ name: f.name, data: f.data }));
      entries.push({
        name: `${variableName}_animation.${video.ext}`,
        data: video.data,
      });
      const zipBlob = _buildZipBlob(entries);
      const url = URL.createObjectURL(zipBlob);
      _downloadDataURL(url, `${variableName}_animation.zip`);
      setTimeout(() => URL.revokeObjectURL(url), 3000);
      window.__captureFrames = [];
      _stopCaptureStream();
    })
    .catch((err) => {
      console.warn("[capture] Video encoding failed, saving PNGs only:", err);
      const entries = frames.map((f) => ({ name: f.name, data: f.data }));
      const zipBlob = _buildZipBlob(entries);
      const url = URL.createObjectURL(zipBlob);
      _downloadDataURL(url, `${variableName}_animation.zip`);
      setTimeout(() => URL.revokeObjectURL(url), 3000);
      window.__captureFrames = [];
      _stopCaptureStream();
    });
}

// Expose capture functions on window for JSEval access
window.captureCollectFrame = captureCollectFrame;
window.captureDownloadZip = captureDownloadZip;

window.trame.utils.quickview = {
  capturePanel,
  formatRange(value, useLog, rangeMin, rangeMax) {
    if (value === null || value === undefined || isNaN(value)) {
      return "Auto";
    }
    if (useLog === "log" && value > 0) {
      return `10^(${Math.log10(value).toFixed(1)})`;
    }
    if (useLog === "symlog") {
      if (value === 0) return "0";
      const linthresh =
        Math.max(Math.abs(rangeMin), Math.abs(rangeMax)) * 1e-2 || 1.0;
      const absVal = Math.abs(value);
      if (absVal <= linthresh) {
        return value.toExponential(1);
      }
      const sign = value < 0 ? "-" : "";
      return `${sign}10^(${Math.log10(absVal).toFixed(1)})`;
    }
    const nSignDigit = Math.log10(Math.abs(value));
    if (Math.abs(nSignDigit) < 6 || value === 0) {
      if (nSignDigit > 0 && nSignDigit < 3) {
        return new Intl.NumberFormat("US", { maximumFractionDigits: 2 }).format(
          value,
        );
      }
      if (nSignDigit > 3) {
        return new Intl.NumberFormat("US", { maximumFractionDigits: 0 }).format(
          value,
        );
      }

      return new Intl.NumberFormat().format(value);
    }
    return value.toExponential(1);
  },
  cols(size) {
    if (size === 1) {
      return 12;
    }
    if (size === 2) {
      return 6;
    }
    if (size === 3) {
      return 4;
    }
    if (size % 3 === 0 || (size + 1) % 3 === 0) {
      return 4;
    }
    if (size % 2 === 0) {
      return 6;
    }
    return 4;
  },
  filter(value, query, item) {
    QUERY_FILTER.updateQuery(query);
    return QUERY_FILTER.keepItem(item.raw);
  },
};
