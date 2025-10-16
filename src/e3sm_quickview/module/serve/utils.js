window.trame.utils.quickview = {
    formatRange(value, useLog) {
        if (value === null || value === undefined || isNaN(value)) {
            return 'Auto';
        }
        if (useLog && value > 0) {
            return `10^(${Math.log10(value).toFixed(1)})`;
        }
        return value.toExponential(1);
    }
}
