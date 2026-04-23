// ZIP - start
// CRC-32 lookup table
const crc32Table = (() => {
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

function crc32(data) {
  let crc = 0xffffffff;
  for (let i = 0; i < data.length; i++) {
    crc = crc32Table[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function dosDateTime() {
  const d = new Date();
  const time =
    (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1);
  const date =
    ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
  return { time, date };
}

function buildZipBlob(entries) {
  // entries: [{name: string, data: Uint8Array}, ...]
  const parts = [];
  const centralDir = [];
  let offset = 0;
  const { time: dosTime, date: dosDate } = dosDateTime();

  for (const file of entries) {
    const nameBytes = new TextEncoder().encode(file.name);
    const data = file.data;
    const crc = crc32(data);

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

// ZIP - end
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

const QUERY_FILTER = new QueryFilter();

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function findContainerToCapture(varName) {
  const query = varName
    ? `.v-card[data-field-name="${varName}"]`
    : ".all-variables";
  return document.querySelector(query);
}

function getFileName(fieldName) {
  const state = trame.state.state;
  const nameTokens = [fieldName || "FullPanel"];
  state.available_animation_tracks.forEach((n) => {
    nameTokens.push(n);
    const nDigit = Math.floor(Math.log10(state[n].length) + 1);
    const idx = state[`${n}_idx`];
    nameTokens.push(String(idx).padStart(nDigit, "0"));
  });
  return `${nameTokens.join("-")}.png`;
}

function downloadURL(dataURL, filename) {
  const a = document.createElement("a");
  a.href = dataURL;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

window.trame.utils.quickview = {
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
  async capturePanel(fieldName) {
    const fileName = getFileName(fieldName);
    const canvas = await html2canvas(findContainerToCapture(fieldName));
    const dataURL = canvas.toDataURL("image/png");
    downloadURL(dataURL, fileName);
  },
  async captureAnimation(selectedFields) {
    const entries = [];
    const exportFields = selectedFields.filter((v) => v !== null);
    const state = trame.state.state;
    const animateName = state.animation_track;
    const nValues = state[animateName].length;
    const idxKey = `${animateName}_idx`;

    trame.state.set("show_animation_export_menu", false);
    trame.state.set("animation_export", true);

    for (let i = 0; i < nValues; i++) {
      trame.state.set(idxKey, i);

      await sleep(0.1);
      await trame.trigger("wait_render");
      await sleep(0.1);

      if (!state.animation_export) {
        break;
      }
      for (let field of exportFields) {
        const name = getFileName(field);
        const canvas = await html2canvas(findContainerToCapture(field));
        const dataURL = canvas.toDataURL("image/png");
        const binary = atob(dataURL.split(",")[1]);
        const data = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) data[i] = binary.charCodeAt(i);
        entries.push({ name, data });
      }
    }
    trame.utils.download("quickview-animation.zip", buildZipBlob(entries));
    trame.state.set("animation_export", false);
  },
};
