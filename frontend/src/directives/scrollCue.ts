import type { Directive } from 'vue'

/**
 * v-scroll-cue: shows a fade on the left/right edge of a PrimeVue DataTable
 * while there are columns scrolled out of view, so it's obvious on a phone
 * that the table scrolls sideways.
 *
 * Put it on the <DataTable> itself (it binds to the table's root element).
 * When the last column is frozen to the right (e.g. Actions), the right-hand
 * fade sits just left of that column instead of covering it.
 *
 * Styles live in main.css under `.scroll-cue`.
 */

interface CueState {
  container: HTMLElement
  update: () => void
  ro: ResizeObserver
}

const states = new WeakMap<HTMLElement, CueState>()

function setup(root: HTMLElement) {
  const container = root.querySelector<HTMLElement>('.p-datatable-table-container')
  if (!container) return

  root.classList.add('scroll-cue')

  const update = () => {
    const max = container.scrollWidth - container.clientWidth
    const left = container.scrollLeft
    root.toggleAttribute('data-more-left', left > 1)
    root.toggleAttribute('data-more-right', max - left > 1)

    // Keep the fades inside the scrolling area (not over a paginator or header above it)
    root.style.setProperty('--cue-top', `${container.offsetTop}px`)
    root.style.setProperty('--cue-height', `${container.offsetHeight}px`)

    // If the last header cell is frozen, keep the right fade clear of it
    const headCells = container.querySelectorAll<HTMLElement>('thead > tr > th')
    const last = headCells[headCells.length - 1]
    const rightInset = last?.classList.contains('p-datatable-frozen-column') ? last.offsetWidth : 0
    root.style.setProperty('--cue-right', `${rightInset}px`)
  }

  const ro = new ResizeObserver(update)
  ro.observe(container)
  const table = container.querySelector('table')
  if (table) ro.observe(table)
  container.addEventListener('scroll', update, { passive: true })

  states.set(root, { container, update, ro })
  update()
}

function teardown(root: HTMLElement) {
  const s = states.get(root)
  if (!s) return
  s.ro.disconnect()
  s.container.removeEventListener('scroll', s.update)
  states.delete(root)
}

declare module 'vue' {
  interface GlobalDirectives {
    vScrollCue: Directive<HTMLElement>
  }
}

export const vScrollCue: Directive<HTMLElement> = {
  mounted(el) {
    setup(el)
  },
  updated(el) {
    // Rows change (data loaded, filtered) -> re-measure; set up late if the container wasn't there yet
    const s = states.get(el)
    if (s) s.update()
    else setup(el)
  },
  unmounted(el) {
    teardown(el)
  },
}
