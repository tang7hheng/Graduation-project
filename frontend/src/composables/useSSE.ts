/**
 * SSE consumer for POST /api/v1/chat.
 *
 * Uses fetch + ReadableStream (instead of EventSource) because
 * EventSource does not support POST request bodies.
 */

export interface SSEHandlers {
  onToken: (text: string) => void
  onSources?: (sources: any[]) => void
  onProductCards?: (cards: any[]) => void
  onDone?: (messageId?: number) => void
  onError?: (msg: string) => void
}

export interface SSEAbortController {
  abort: () => void
}

export async function streamChat(
  sessionId: string,
  message: string,
  handlers: SSEHandlers,
): Promise<SSEAbortController> {
  const controller = new AbortController()

  const run = async () => {
    let resp: Response
    try {
      resp = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message }),
        signal: controller.signal,
      })
    } catch (e: any) {
      if (e.name === 'AbortError') return
      handlers.onError?.(e.message || '网络错误')
      return
    }

    if (!resp.ok) {
      const text = await resp.text().catch(() => '')
      let detail = `HTTP ${resp.status}`
      try {
        const j = JSON.parse(text)
        detail = j.detail || detail
      } catch {
        /* ignore */
      }
      handlers.onError?.(detail)
      return
    }

    if (!resp.body) {
      handlers.onError?.('响应体为空')
      return
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // SSE frames are separated by \n\n
        let sepIndex: number
        while ((sepIndex = buffer.indexOf('\n\n')) >= 0) {
          const frame = buffer.slice(0, sepIndex)
          buffer = buffer.slice(sepIndex + 2)
          handleFrame(frame, handlers)
        }
      }
      // Flush trailing frame if any
      if (buffer.trim()) handleFrame(buffer, handlers)
    } catch (e: any) {
      if (e.name === 'AbortError') return
      handlers.onError?.(e.message || '流读取失败')
    }
  }

  void run()
  return { abort: () => controller.abort() }
}

function handleFrame(frame: string, h: SSEHandlers) {
  // Expect lines like: data: {...}
  const lines = frame.split('\n')
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed.startsWith('data:')) continue
    const payload = trimmed.slice(5).trim()
    if (!payload) continue
    try {
      const evt = JSON.parse(payload)
      dispatchEvent(evt, h)
    } catch {
      // ignore malformed
    }
  }
}

function dispatchEvent(evt: any, h: SSEHandlers) {
  switch (evt?.type) {
    case 'token':
      h.onToken(evt.content || '')
      break
    case 'sources':
      h.onSources?.(evt.sources || [])
      break
    case 'product_cards':
      h.onProductCards?.(evt.product_cards || [])
      break
    case 'done':
      h.onDone?.(evt.message_id)
      break
    case 'error':
      h.onError?.(evt.message || '未知错误')
      break
    case 'ping':
      // keep-alive, ignore
      break
    default:
      // Unknown event type; ignore
      break
  }
}
