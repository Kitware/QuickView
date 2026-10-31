---
title: Gallery
outline: false
sidebar: false
pageClass: gallery-page
---

<script setup>
import ExampleGallery from './components/ExampleGallery.vue'
import { data as examples } from './examples.data.js'
</script>

# Gallery

*Examples of visualization from the QuickView family of tools.*

Filter the examples below, then select a preview to enlarge screenshots or watch a recording.

<ExampleGallery :examples="examples" />
