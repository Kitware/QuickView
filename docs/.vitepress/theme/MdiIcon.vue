<script setup>
import {
  mdiCameraOutline,
  mdiChevronLeft,
  mdiChevronRight,
  mdiCloseCircle,
  mdiCloseOctagonOutline,
  mdiDatabase,
  mdiDatabasePlus,
  mdiDatabaseRefreshOutline,
  mdiDownloadMultipleOutline,
  mdiEarth,
  mdiEyeCheckOutline,
  mdiEyeOutline,
  mdiEyeRemoveOutline,
  mdiFileDownloadOutline,
  mdiFileUploadOutline,
  mdiFitToPageOutline,
  mdiFolderArrowLeftRightOutline,
  mdiFolderUploadOutline,
  mdiFormatColorFill,
  mdiHome,
  mdiListStatus,
  mdiPageFirst,
  mdiPageLast,
  mdiPlay,
  mdiStop,
  mdiTuneVariant,
  mdiVectorPolylinePlus,
  mdiVideo,
  mdiViewModule,
  mdiWeb,
} from "@mdi/js";

defineProps({
  name: { type: String, required: true },
  label: { type: String, default: "" },
  iconFirst: Boolean,
  reverse: Boolean,
});

const paths = {
  "mdi-camera-outline": mdiCameraOutline,
  "mdi-chevron-left": mdiChevronLeft,
  "mdi-chevron-right": mdiChevronRight,
  "mdi-close-circle": mdiCloseCircle,
  "mdi-close-octagon-outline": mdiCloseOctagonOutline,
  "mdi-database": mdiDatabase,
  "mdi-database-plus": mdiDatabasePlus,
  "mdi-database-refresh-outline": mdiDatabaseRefreshOutline,
  "mdi-download-multiple-outline": mdiDownloadMultipleOutline,
  "mdi-earth": mdiEarth,
  "mdi-eye-check-outline": mdiEyeCheckOutline,
  "mdi-eye-outline": mdiEyeOutline,
  "mdi-eye-remove-outline": mdiEyeRemoveOutline,
  "mdi-file-download-outline": mdiFileDownloadOutline,
  "mdi-file-upload-outline": mdiFileUploadOutline,
  "mdi-fit-to-page-outline": mdiFitToPageOutline,
  "mdi-folder-arrow-left-right-outline": mdiFolderArrowLeftRightOutline,
  "mdi-folder-upload-outline": mdiFolderUploadOutline,
  "mdi-format-color-fill": mdiFormatColorFill,
  "mdi-home": mdiHome,
  "mdi-list-status": mdiListStatus,
  "mdi-page-first": mdiPageFirst,
  "mdi-page-last": mdiPageLast,
  "mdi-play": mdiPlay,
  "mdi-stop": mdiStop,
  "mdi-tune-variant": mdiTuneVariant,
  "mdi-vector-polyline-plus": mdiVectorPolylinePlus,
  "mdi-video": mdiVideo,
  "mdi-view-module": mdiViewModule,
  "mdi-web": mdiWeb,
};
</script>

<template>
  <span class="mdi-inline" :class="{ 'mdi-icon-only': !label, 'mdi-icon-first': iconFirst }">
    <template v-if="label && !iconFirst"><strong>{{ label }}</strong>&nbsp;</template
    ><span aria-hidden="true"
      >{{ label && !iconFirst ? "(" : "" }}<svg :class="{ reverse }" viewBox="0 0 24 24" focusable="false">
        <path :d="paths[name]" /></svg
      >{{ label && !iconFirst ? ")" : "" }}</span
    ><template v-if="label && iconFirst">&nbsp;<strong>{{ label }}</strong></template>
  </span>
</template>

<style scoped>
.mdi-inline > [aria-hidden="true"],
.mdi-icon-first {
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

.mdi-icon-only svg {
  width: 24px;
  height: 24px;
  vertical-align: middle;
}
</style>
