# PhysioAssist AI Chatbot Backend

A FastAPI backend implementation of a chatbot using Microsoft Autogen AgentChat with **persistent file-based chat history** per session.

## Features

✅ **Session-based chat** - Each chat has a unique ID  
✅ **Persistent memory** - Chat history stored in local JSON files  
✅ **Context-aware** - Agent remembers previous messages in the conversation  
✅ **RESTful API** - Easy integration with any frontend  
✅ **Swagger UI** - Interactive API documentation  
✅ **Session management** - View, list, and delete chat sessions

## Project Structure

```
src2/
├── server.py          # FastAPI server with chat endpoints
├── file_memory.py     # Custom FileMemory class for persistence
├── requirements.txt   # Python dependencies
├── README.md         # This file
└── user_chats/       # Directory for chat session files (auto-created)
    ├── {chat_id_1}.json
    ├── {chat_id_2}.json
    └── ...
```

## Prerequisites

- Python 3.10 or higher
- OpenAI API key

## Installation

1. **Navigate to the src2 directory:**
   ```bash
   cd src2
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your OpenAI API key:**
   
   Create a `.env` file in the src2 directory:
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```
   
   Or export it directly:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Running the Server

Start the server with:

```bash
python server.py
```

Or using uvicorn directly:

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## Testing with Swagger UI

1. **Open your browser and go to:**
   ```
   http://localhost:8000/docs
   ```

2. **Test the chat endpoint:**
   
   - Click on `POST /chat`
   - Click "Try it out"
   - Use this example request:
   
   ```json
   {
     "chat_id": null,
     "message": "Hello! Can you help me with physiotherapy?"
   }
   ```
   
   - Click "Execute"
   - **Copy the `chat_id` from the response!**

3. **Continue the conversation:**
   
   - Use the same endpoint again
   - This time, include the `chat_id` you copied:
   
   ```json
   {
     "chat_id": "550e8400-e29b-41d4-a716-446655440000",
     "message": "What exercises are good for back pain?"
   }
   ```
   
   - The bot will remember your previous messages!

4. **View chat history:**
   
   - Click on `GET /chat/{chat_id}/history`
   - Enter your `chat_id`
   - See the full conversation history

## API Endpoints

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message and get a response |
| `GET` | `/chat/{chat_id}/history` | Get full chat history for a session |
| `DELETE` | `/chat/{chat_id}` | Delete a chat session |
| `GET` | `/sessions` | List all active chat sessions |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |

## Example Usage with curl

**Start a new conversation:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! Tell me about physiotherapy."}'
```

**Continue with a specific session:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "your-chat-id-here",
    "message": "What about shoulder exercises?"
  }'
```

**Get chat history:**
```bash
curl "http://localhost:8000/chat/your-chat-id-here/history"
```

**List all sessions:**
```bash
curl "http://localhost:8000/sessions"
```

## How It Works

1. **Incoming Message** - Frontend sends a message with optional `chat_id`
2. **Load History** - Server loads existing chat history from `user_chats/{chat_id}.json`
3. **Add to Memory** - New message is added to the memory buffer
4. **Agent Processing** - Autogen AssistantAgent processes the message with full context
5. **Save Response** - AI response is saved back to the file
6. **Return Result** - Server returns the response with the `chat_id`

## Chat History File Format

Each session is stored as a JSON file:

```json
[
  {
    "content": "Hello! Can you help me with physiotherapy?",
    "mime_type": "TEXT",
    "metadata": {"role": "user"}
  },
  {
    "content": "Of course! I'd be happy to help with physiotherapy questions...",
    "mime_type": "TEXT",
    "metadata": {"role": "assistant"}
  }
]
```

## Customization

### Change the AI Model

In [server.py](server.py#L73), modify the model:

```python
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",  # or "gpt-4-turbo", "gpt-3.5-turbo"
)
```

### Customize System Message

In [server.py](server.py#L77), change the assistant's behavior:

```python
assistant_agent = AssistantAgent(
    name="PhysioAssist",
    model_client=model_client,
    system_message="Your custom system message here...",
)
```

### Change Storage Location

In [server.py](server.py#L21), modify the directory:

```python
USER_CHATS_DIR = "your_custom_directory"
```

## Troubleshooting

**Import errors?**
- Make sure all dependencies are installed: `pip install -r requirements.txt`

**OpenAI API errors?**
- Verify your API key is set: `echo $OPENAI_API_KEY`
- Check you have credits in your OpenAI account

**Chat history not persisting?**
- Check that the `user_chats/` directory exists and is writable
- Look for error messages in the server console

**Server won't start?**
- Check if port 8000 is already in use
- Try a different port: `python server.py --port 8001`

## Frontend Integration

To connect a frontend (React, Vue, Angular, etc.):

```javascript
// Example fetch call
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    chat_id: chatId || null,  // null for new chat
    message: userMessage
  })
});

const data = await response.json();
// Save data.chat_id for subsequent messages
// Display data.response to user
```

## Next Steps

- Add authentication for multi-user support
- Implement semantic search in chat history
- Add tools (calculator, search, etc.) to the agent
- Integrate with vector database for RAG
- Add rate limiting and caching

## License

MIT License - feel free to use and modify!

---

**Need help?** Check the Swagger docs at `/docs` or see the [Autogen documentation](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html).
