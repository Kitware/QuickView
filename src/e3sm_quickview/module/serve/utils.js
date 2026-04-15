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
};
