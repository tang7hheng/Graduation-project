import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSource, MessageOut, ProductCard } from '@/api/client'
import { http } from '@/api/client'
import { streamChat, type SSEAbortController } from '@/composables/useSSE'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<MessageOut[]>([])
  const streamingText = ref<string>('')
  const isStreaming = ref<boolean>(false)
  const currentSources = ref<ChatSource[]>([])
  const currentProductCards = ref<ProductCard[]>([])
  const errorMessage = ref<string>('')
  const currentSessionId = ref<string>('')
  let abortController: SSEAbortController | null = null

  function reset() {
    abortController?.abort()
    abortController = null
    messages.value = []
    streamingText.value = ''
    isStreaming.value = false
    currentSources.value = []
    currentProductCards.value = []
    errorMessage.value = ''
    currentSessionId.value = ''
  }

  async function loadSession(sessionId: string) {
    reset()
    currentSessionId.value = sessionId
    const { data } = await http.get(`/sessions/${sessionId}`)
    messages.value = (data.messages as MessageOut[]) || []
  }

  async function sendMessage(text: string) {
    const trimmed = text.trim()
    if (!trimmed || isStreaming.value) return
    if (!currentSessionId.value) {
      errorMessage.value = '当前没有选中会话'
      return
    }

    errorMessage.value = ''
    currentSources.value = []
    currentProductCards.value = []

    // Optimistically append the user message
    const optimisticUser: MessageOut = {
      id: -Math.floor(Math.random() * 1e9),
      session_id: currentSessionId.value,
      role: 'user',
      content: trimmed,
      sources_json: [],
      product_cards_json: [],
      created_at: new Date().toISOString(),
    }
    messages.value.push(optimisticUser)

    isStreaming.value = true
    streamingText.value = ''

    abortController = await streamChat(currentSessionId.value, trimmed, {
      onToken: (t) => {
        streamingText.value += t
      },
      onSources: (sources) => {
        currentSources.value = sources
      },
      onProductCards: (cards) => {
        currentProductCards.value = cards
      },
      onDone: (messageId) => {
        const finalText = streamingText.value
        messages.value.push({
          id: messageId ?? -Math.floor(Math.random() * 1e9),
          session_id: currentSessionId.value,
          role: 'assistant',
          content: finalText,
          sources_json: [...currentSources.value],
          product_cards_json: [...currentProductCards.value],
          created_at: new Date().toISOString(),
        })
        streamingText.value = ''
        currentProductCards.value = []
        isStreaming.value = false
        abortController = null
      },
      onError: (msg) => {
        errorMessage.value = msg
        // Save partial streaming text if any
        if (streamingText.value) {
          messages.value.push({
            id: -Math.floor(Math.random() * 1e9),
            session_id: currentSessionId.value,
            role: 'assistant',
            content: streamingText.value + `\n\n_[错误: ${msg}]_`,
            sources_json: [],
            product_cards_json: [],
            created_at: new Date().toISOString(),
          })
          streamingText.value = ''
        }
        isStreaming.value = false
        abortController = null
      },
    })
  }

  function stopStreaming() {
    abortController?.abort()
    abortController = null
    if (streamingText.value) {
      messages.value.push({
        id: -Math.floor(Math.random() * 1e9),
        session_id: currentSessionId.value,
        role: 'assistant',
        content: streamingText.value + '\n\n_[已中止]_',
        sources_json: [],
        product_cards_json: [],
        created_at: new Date().toISOString(),
      })
      streamingText.value = ''
    }
    isStreaming.value = false
  }

  return {
    messages,
    streamingText,
    isStreaming,
    currentSources,
    currentProductCards,
    errorMessage,
    currentSessionId,
    reset,
    loadSession,
    sendMessage,
    stopStreaming,
  }
})
