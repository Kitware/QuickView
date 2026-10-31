import { createContentLoader } from 'vitepress'

// Only metadata goes into the gallery bundle; explanations stay on example pages.
export default createContentLoader('gallery/examples/*.md', {
  transform(pages) {
    const ids = new Set()
    return pages.map(({ url, frontmatter: example }) => {
      if (!example.id || ids.has(example.id)) {
        throw new Error(`Gallery example needs a unique id: ${url}`)
      }
      ids.add(example.id)
      for (const field of ['tools', 'models', 'gridConfigurations', 'gridRepresentations', 'meshDesignations', 'images']) {
        if (!Array.isArray(example[field]) || !example[field].length) {
          throw new Error(`Missing gallery field ${field}: ${url}`)
        }
      }
      for (const media of example.images) {
        if (!media.src || !media.alt || !media.caption) {
          throw new Error(`Gallery media needs src, alt and caption: ${url}`)
        }
      }
      return { ...example, url }
    }).sort((a, b) => (a.order ?? 100) - (b.order ?? 100) || a.title.localeCompare(b.title))
  }
})
