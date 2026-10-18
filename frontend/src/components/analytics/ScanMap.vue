<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { ScanLocation } from '@/api/analytics'

const props = defineProps<{
  locations: ScanLocation[]
}>()

const MARKER_COLOR = '#6366f1'
const MIN_RADIUS = 5
const MAX_RADIUS = 26

const container = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let markerLayer: L.LayerGroup | null = null

const regionNames = new Intl.DisplayNames(['en'], { type: 'region' })

function placeLabel(loc: ScanLocation): string {
  let country = loc.country ?? ''
  try {
    if (country) country = regionNames.of(country) ?? country
  } catch { /* keep ISO code */ }
  return [loc.city, loc.region, country].filter(Boolean).join(', ') || 'Unknown location'
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, c => `&#${c.charCodeAt(0)};`)
}

function renderMarkers() {
  if (!map || !markerLayer) return
  markerLayer.clearLayers()
  if (!props.locations.length) return

  const max = Math.max(...props.locations.map(l => l.count))
  const bounds = L.latLngBounds([])

  // Draw largest first so smaller circles stay on top and remain hoverable
  for (const loc of [...props.locations].sort((a, b) => b.count - a.count)) {
    const latlng = L.latLng(loc.latitude, loc.longitude)
    // Area (not radius) proportional to count, so big cities don't dwarf everything
    const radius = MIN_RADIUS + Math.sqrt(loc.count / max) * (MAX_RADIUS - MIN_RADIUS)
    L.circleMarker(latlng, {
      radius,
      color: MARKER_COLOR,
      weight: 1.5,
      fillColor: MARKER_COLOR,
      fillOpacity: 0.45,
    })
      .bindTooltip(
        `<strong>${escapeHtml(placeLabel(loc))}</strong><br>${loc.count.toLocaleString()} scan${loc.count === 1 ? '' : 's'}`,
        { direction: 'top', offset: [0, -radius] },
      )
      .addTo(markerLayer)
    bounds.extend(latlng)
  }

  map.fitBounds(bounds, { padding: [40, 40], maxZoom: 6 })
}

onMounted(() => {
  if (!container.value) return
  map = L.map(container.value, {
    preferCanvas: true,      // canvas renderer – stays fast with thousands of circles
    worldCopyJump: true,
    minZoom: 1,
    scrollWheelZoom: false,  // don't hijack page scrolling; zoom with +/- or ctrl-scroll
  }).setView([20, 0], 2)

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
  }).addTo(map)

  markerLayer = L.layerGroup().addTo(map)
  renderMarkers()
})

watch(() => props.locations, renderMarkers)

onBeforeUnmount(() => {
  map?.remove()
  map = null
  markerLayer = null
})
</script>

<template>
  <div ref="container" class="scan-map" />
</template>

<style>
.scan-map {
  height: 420px;
  width: 100%;
  border-radius: 0.5rem;
  /* Leaflet panes use z-index up to 1000; keep them from covering dropdowns/sidebar */
  isolation: isolate;
  z-index: 0;
  background-color: var(--bg-elevated);
}

/* OSM has no dark tile set – invert the light tiles in dark mode */
html.dark .scan-map .leaflet-tile-pane {
  filter: invert(1) hue-rotate(180deg) brightness(0.9) contrast(0.9);
}

html.dark .scan-map .leaflet-control-attribution,
html.dark .scan-map .leaflet-bar a {
  background-color: var(--bg-card);
  color: var(--text-secondary);
  border-color: var(--border);
}

html.dark .scan-map .leaflet-control-attribution a {
  color: var(--text-secondary);
}
</style>
