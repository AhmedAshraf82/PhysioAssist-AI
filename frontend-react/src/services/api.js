import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8002",
  timeout: 90000,
});

export async function healthCheck() {
  const { data } = await api.get("/health");
  return data;
}

export async function runIngestion(recreateIndex = false) {
  const { data } = await api.post("/data/ingest", { recreate_index: recreateIndex });
  return data;
}

export async function searchInjuries(query) {
  const { data } = await api.post("/search/", { query });
  return data;
}

export async function listSessions() {
  const { data } = await api.get("/prediagnose/sessions");
  return data;
}

export async function getChatHistory(chatId) {
  const { data } = await api.get(`/prediagnose/${chatId}/history`);
  return data;
}

export async function sendChatMessage(message, chatId) {
  const payload = chatId ? { message, chat_id: chatId } : { message };
  const { data } = await api.post("/prediagnose", payload);
  return data;
}
