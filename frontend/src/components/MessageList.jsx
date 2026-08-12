import MessageBubble from './MessageBubble'

export default function MessageList({ messages, handleRegenerate, messagesEndRef }) {
  return (
    <div className="flex-1 overflow-y-auto px-4 pt-4">
      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          onRegenerate={msg.role === 'assistant' && !msg.streaming ? handleRegenerate : null}
        />
      ))}

      <div ref={messagesEndRef} />
    </div>
  )
}
