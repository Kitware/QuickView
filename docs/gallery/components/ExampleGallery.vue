<script setup>
import { computed, nextTick, onBeforeUnmount, reactive, ref } from 'vue'
import { withBase } from 'vitepress'

const props = defineProps({ examples: { type: Array, required: true } })
const groups = [
  { key: 'tools', label: 'Tool' },
  { key: 'models', label: 'Model' },
  { key: 'gridConfigurations', label: 'Grid configuration' },
  { key: 'gridRepresentations', label: 'Grid representation' },
  { key: 'meshDesignations', label: 'Mesh designation' },
]
const selected = reactive(Object.fromEntries(groups.map(({ key }) => [key, []])))
const filters = computed(() => groups.map(group => ({
  ...group,
  values: [...new Set(props.examples.flatMap(example => example[group.key]))].sort(),
})))
const filtered = computed(() => props.examples.filter(example => groups.every(({ key }) =>
  !selected[key].length || selected[key].some(value => example[key].includes(value)),
)))
const activeCount = computed(() => Object.values(selected).flat().length)
function clearFilters() { groups.forEach(({ key }) => { selected[key] = [] }) }

// These files already live in docs/gallery. Let Vite emit their hashed URLs;
// a raw /gallery/... URL alone would bypass Vite's asset handling.
const assets = import.meta.glob('../*.{png,jpg,jpeg,webp,avif,gif,svg,mp4,webm}', {
  eager: true, query: '?url', import: 'default',
})
function assetUrl(path) {
  if (!path) return ''
  if (path.startsWith('/gallery/')) {
    return assets[`../${path.slice('/gallery/'.length)}`] || withBase(path)
  }
  return /^(https?:)?\/\//.test(path) ? path : withBase(path)
}
const active = ref(null)
const mediaIndex = ref(0)
const media = computed(() => active.value?.images[mediaIndex.value])
const dialog = ref(null)
let previousFocus = null
let originalOverflow = ''
async function openExample(example, index = 0) {
  previousFocus = document.activeElement
  active.value = example
  mediaIndex.value = index
  await nextTick()
  originalOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  dialog.value.showModal()
  dialog.value.querySelector('[data-close]').focus()
}
function closeDialog() { dialog.value?.close() }
function afterClose() {
  dialog.value?.querySelector('video')?.pause()
  active.value = null
  document.body.style.overflow = originalOverflow
  previousFocus?.focus()
}
function changeMedia(step) {
  mediaIndex.value = (mediaIndex.value + step + active.value.images.length) % active.value.images.length
}
function onKeydown(event) {
  // Leave arrow keys available to native video controls.
  if (event.target.closest('video') || active.value?.images.length < 2) return
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault()
    changeMedia(event.key === 'ArrowLeft' ? -1 : 1)
  }
}
onBeforeUnmount(() => {
  if (active.value) document.body.style.overflow = originalOverflow
})
</script>

<template>
  <div class="example-gallery">
    <section class="gallery-filters" aria-label="Filter gallery examples">
      <fieldset v-for="group in filters" :key="group.key">
        <legend>{{ group.label }}</legend>
        <div class="filter-options">
          <label v-for="value in group.values" :key="value" class="filter-choice">
            <input v-model="selected[group.key]" type="checkbox" :value="value">
            <span>{{ value }}</span>
          </label>
        </div>
      </fieldset>
      <p class="filter-help">Selections within a group match any selected tag; selections across groups must all match.</p>
      <div class="gallery-results">
        <span role="status" aria-live="polite">Showing {{ filtered.length }} of {{ examples.length }} examples</span>
        <button type="button" :disabled="!activeCount" @click="clearFilters">Clear filters</button>
      </div>
    </section>

    <div v-if="filtered.length" class="gallery-grid">
      <article v-for="example in filtered" :id="example.id" :key="example.id" class="gallery-card">
        <span v-for="alias in example.aliases || []" :id="alias" :key="alias" class="legacy-anchor" />
        <button type="button" class="preview-button" :aria-label="`Open ${example.title}`" @click="openExample(example)">
          <img v-if="example.thumbnail || example.images[0].poster || example.images[0].type !== 'video'"
            :src="assetUrl(example.thumbnail || example.images[0].poster || example.images[0].src)"
            :alt="example.images[0].alt" loading="lazy" decoding="async">
          <span v-else class="video-preview"><span aria-hidden="true">▶</span> Watch recording</span>
          <span class="preview-label">{{ example.images[0].type === 'video' ? 'Video' : example.images.length > 1 ? `${example.images.length} images · Enlarge` : 'Enlarge' }}</span>
        </button>
        <div class="card-content">
          <h2><a :href="withBase(example.url)">{{ example.title }}</a></h2>
          <p>{{ example.summary }}</p>
          <ul class="gallery-tags" aria-label="Example tags">
            <li v-for="tag in [...example.tools, ...example.models, ...example.gridConfigurations, ...example.gridRepresentations, ...example.meshDesignations]" :key="tag">{{ tag }}</li>
          </ul>
          <p class="mesh-label">{{ example.mesh }}</p>
          <a class="details-link" :href="withBase(example.url)">Details and credits →</a>
        </div>
      </article>
    </div>
    <p v-else class="gallery-empty">No examples match these filters. Clear filters or select fewer tags.</p>

    <dialog ref="dialog" class="gallery-dialog" aria-labelledby="gallery-dialog-title" @close="afterClose" @keydown="onKeydown" @click="event => { if (event.target === dialog) closeDialog() }">
      <div v-if="active" class="dialog-content">
        <header>
          <h2 id="gallery-dialog-title">{{ active.title }}</h2>
          <button type="button" data-close aria-label="Close enlarged preview" @click="closeDialog">Close ✕</button>
        </header>
        <div class="dialog-media" :key="media.src">
          <video v-if="media.type === 'video'" controls playsinline preload="metadata" :src="assetUrl(media.src)" :aria-label="media.alt" :poster="media.poster ? assetUrl(media.poster) : undefined">
            Your browser does not support embedded video. Use the original-file link below.
          </video>
          <img v-else :src="assetUrl(media.src)" :alt="media.alt">
        </div>
        <nav v-if="active.images.length > 1" class="media-navigation" aria-label="Images in this example">
          <button type="button" @click="changeMedia(-1)">← Previous</button>
          <span role="status" aria-live="polite">{{ mediaIndex + 1 }} / {{ active.images.length }}</span>
          <button type="button" @click="changeMedia(1)">Next →</button>
        </nav>
        <p class="media-caption">{{ media.caption }}</p>
        <p class="media-credit">{{ active.credit }}</p>
        <footer>
          <a :href="assetUrl(media.src)" target="_blank" rel="noopener">Open original {{ media.type === 'video' ? 'recording' : 'image' }} ↗</a>
          <a :href="withBase(active.url)">Details and credits →</a>
        </footer>
      </div>
    </dialog>
  </div>
</template>

<style scoped>
.example-gallery { margin-top: 1.5rem; }
.gallery-filters { padding: 1rem 1.25rem; background: color-mix(in srgb, var(--vp-c-brand-1) 10%, transparent); border: 1px solid var(--vp-c-divider); border-radius: 12px; }
.gallery-filters fieldset { display: flex; flex-wrap: wrap; gap: .5rem 1rem; margin: 0 0 .75rem; padding: 0; border: 0; min-width: 0; }
.gallery-filters legend { float: left; width: 10rem; padding: .3rem 0; font-size: .9rem; font-weight: 600; }
.filter-options { display: flex; flex-wrap: wrap; gap: .4rem; }
.filter-choice { display: inline-flex; align-items: center; gap: .35rem; padding: .2rem .65rem; border: 1px solid var(--vp-c-divider); border-radius: 6px; background: var(--vp-c-bg); font-size: .85rem; cursor: pointer; }
.filter-choice:has(input:checked) { border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); }
.filter-choice input { margin: 0; accent-color: var(--vp-c-brand-1); }
.filter-help { font-size: .8rem; color: var(--vp-c-text-2); line-height: 1.5; }
.gallery-results { display: flex; align-items: center; flex-wrap: wrap; justify-content: space-between; gap: .5rem; font-size: .9rem; }
.gallery-results button { padding: .15rem .5rem; border-radius: 12px; background: var(--vp-c-brand-1); border: 1px solid var(--vp-c-divider); color: white; font-size: .75rem; }
.gallery-dialog button { border: 1px solid var(--vp-c-divider); border-radius: 6px; padding: .3rem .7rem; background: var(--vp-c-bg); color: var(--vp-c-text-1); cursor: pointer; font: inherit; }
.gallery-results button:disabled { opacity: .45; cursor: default; }
.gallery-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }
.gallery-card { position: relative; border: 1px solid var(--vp-c-divider); border-radius: 12px; overflow: hidden; background: var(--vp-c-bg); scroll-margin-top: 5rem; }
.legacy-anchor { position: absolute; top: 0; scroll-margin-top: 5rem; }
.preview-button { position: relative; display: flex; width: 100%; align-items: center; justify-content: center; aspect-ratio: 16 / 10; padding: 0; overflow: hidden; border: 0; border-bottom: 1px solid var(--vp-c-divider); background: var(--vp-c-bg-soft); cursor: zoom-in; }
.preview-button img { display: block; width: 100%; height: 100%; object-fit: contain; }
.preview-label { position: absolute; right: .5rem; bottom: .5rem; padding: .15rem .5rem; border-radius: 12px; background: var(--vp-c-brand-1); border: 1px solid var(--vp-c-divider); color: white; font-size: .75rem; }
.video-preview { display: flex; flex-direction: column; gap: .75rem; align-items: center; color: var(--vp-c-text-2); }
.video-preview > span { font-size: 2rem; color: var(--vp-c-brand-1); }
.card-content { padding: 1rem 1.2rem 1.2rem; }
.card-content h2 { margin: 0; padding: 0; border: 0; font-size: 1.1rem; line-height: 1.5; letter-spacing: normal; }
.card-content h2 a { color: var(--vp-c-text-1); text-decoration: none; }
.card-content p { font-size: .9rem; line-height: 1.65; margin: .6rem 0; }
.gallery-tags { display: flex; flex-wrap: wrap; gap: .35rem; list-style: none; margin: .85rem 0; padding: 0; }
.gallery-tags li { margin: 0; padding: .1rem .45rem; border-radius: 4px; background: var(--vp-c-bg-soft); font-size: .75rem; color: var(--vp-c-text-2); }
.card-content .mesh-label { color: var(--vp-c-text-2); font-size: .8rem; }
.details-link { font-size: .85rem; }
.gallery-empty { padding: 2rem 0; }
.gallery-dialog { width: min(1280px, 95vw); max-width: 95vw; max-height: 92dvh; margin: auto; padding: 0; border: 1px solid var(--vp-c-divider); border-radius: 12px; color: var(--vp-c-text-1); background: var(--vp-c-bg); overflow: auto; }
.gallery-dialog::backdrop { background: rgb(0 0 0 / .75); }
.dialog-content { padding: 1.25rem; }
.dialog-content header { display: flex; align-items: start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
.dialog-content header h2 { margin: 0; border: 0; padding: 0; font-size: 1.1rem; line-height: 1.5; }
.dialog-content header button { flex-shrink: 0; }
.dialog-media { display: flex; align-items: center; justify-content: center; background: var(--vp-c-bg-soft); }
.dialog-media img, .dialog-media video { display: block; max-width: 100%; max-height: 62dvh; object-fit: contain; }
.media-navigation { display: flex; justify-content: space-between; align-items: center; gap: .5rem; margin-top: .75rem; font-size: .9rem; }
.media-caption { margin: .9rem 0 .5rem; font-size: .95rem; line-height: 1.6; }
.media-credit { color: var(--vp-c-text-2); font-size: .85rem; }
.dialog-content footer { display: flex; flex-wrap: wrap; gap: .7rem 1.5rem; font-size: .9rem; }
.example-gallery :focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
@media (max-width: 639px) {
  .gallery-grid { grid-template-columns: 1fr; }
  .gallery-filters legend { float: none; width: auto; }
  .dialog-content { padding: .8rem; }
}
</style>

<style>
/* Give this gallery room for readable scientific screenshots. */
.gallery-page .VPDoc .content-container { max-width: 1120px !important; }
.gallery-page .VPDoc.has-aside .content-container { max-width: 1120px !important; }
.gallery-page .VPDoc .content { max-width: 1200px; }
</style>
