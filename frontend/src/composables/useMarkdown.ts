import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

marked.setOptions({
  breaks: true,
  gfm: true,
})

let debounceTimer: number | null = null

/**
 * Render markdown into sanitized HTML.
 */
export function renderMarkdown(text: string): string {
  const raw = marked.parse(text || '', { async: false }) as string
  return DOMPurify.sanitize(raw)
}

/**
 * Render markdown into a target element's innerHTML, with code highlighting.
 * Debounced for streaming use (avoid re-rendering on every token).
 */
export function renderMarkdownTo(el: HTMLElement, text: string, immediate = false) {
  const apply = () => {
    el.innerHTML = renderMarkdown(text)
    el.querySelectorAll('pre code').forEach((block) => {
      try {
        hljs.highlightElement(block as HTMLElement)
      } catch {
        // ignore
      }
    })
  }

  if (immediate) {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    apply()
    return
  }

  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(apply, 50)
}
