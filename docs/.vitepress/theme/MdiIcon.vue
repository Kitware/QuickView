<script setup>
import {
  mdiChevronLeft,
  mdiChevronRight,
  mdiDownloadMultipleOutline,
  mdiPageFirst,
  mdiPageLast,
  mdiPlay,
  mdiStop,
  mdiTuneVariant,
  mdiVideo,
} from "@mdi/js";

defineProps({
  name: { type: String, required: true },
  label: { type: String, required: true },
  reverse: Boolean,
});

const paths = {
  "mdi-chevron-left": mdiChevronLeft,
  "mdi-chevron-right": mdiChevronRight,
  "mdi-download-multiple-outline": mdiDownloadMultipleOutline,
  "mdi-page-first": mdiPageFirst,
  "mdi-page-last": mdiPageLast,
  "mdi-play": mdiPlay,
  "mdi-stop": mdiStop,
  "mdi-tune-variant": mdiTuneVariant,
  "mdi-video": mdiVideo,
};
</script>

<template>
  <span class="mdi-inline">
    <strong>{{ label }}</strong
    >&nbsp;<span aria-hidden="true"
      >(<svg :class="{ reverse }" viewBox="0 0 24 24" focusable="false">
        <path :d="paths[name]" /></svg
      >)</span
    >
  </span>
</template>

<style scoped>
.mdi-inline {
  white-space: nowrap;
}

.mdi-inline svg {
  display: inline-block;
  width: 1.25em;
  height: 1.25em;
  vertical-align: -0.24em;
  fill: currentColor;
}

.mdi-inline svg.reverse {
  transform: scaleX(-1);
}
</style>
