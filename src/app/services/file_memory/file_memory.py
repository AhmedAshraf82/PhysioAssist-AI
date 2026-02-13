# file_memory.py
import os
import json
from typing import List, Sequence
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType


class FileMemory(Memory):
    """
    Simple file-based memory store.
    Persists MemoryContent items to a local file per chat session.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._buffer: List[MemoryContent] = []
        self._load_file()

    def _load_file(self):
        """Load existing chat history from file if it exists."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for mem in data:
                    self._buffer.append(
                        MemoryContent(
                            content=mem["content"],
                            mime_type=MemoryMimeType[mem["mime_type"]],
                            metadata=mem.get("metadata", {}),
                        )
                    )
            except Exception as e:
                print(f"Error loading memory file: {e}")

    def _save_file(self):
        """Save current memory buffer to file."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(
                    [
                        {
                            "content": m.content,
                            "mime_type": m.mime_type.name,
                            "metadata": m.metadata,
                        }
                        for m in self._buffer
                    ],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            print(f"Error saving memory file: {e}")

    async def add(self, memory: MemoryContent) -> None:
        """Add a new memory item and persist to file."""
        self._buffer.append(memory)
        self._save_file()

    async def query(self, query_str: str) -> List[MemoryContent]:
        """Simple keyword search in memory content."""
        return [m for m in self._buffer if query_str.lower() in m.content.lower()]

    async def update_context(self, query: str) -> None:
        """
        Update context with relevant memories.
        This is called by the agent to retrieve relevant context.
        """
        # For now, return all messages as context
        # You can implement more sophisticated retrieval logic here
        pass

    async def clear(self) -> None:
        """Clear all memory and delete file."""
        self._buffer.clear()
        self._save_file()

    async def close(self) -> None:
        """Save file on close."""
        self._save_file()

    def get_all_messages(self) -> List[MemoryContent]:
        """Get all messages from memory."""
        return self._buffer.copy()
