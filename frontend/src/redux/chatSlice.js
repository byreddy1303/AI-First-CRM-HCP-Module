import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { apiRequest } from "./api";

export const sendChatMessage = createAsyncThunk("chat/send", async (message) => {
  return apiRequest("/api/agent/chat", {
    method: "POST",
    body: JSON.stringify({ message })
  });
});

export const extractInteraction = createAsyncThunk("chat/extract", async (text) => {
  return apiRequest("/api/agent/extract", {
    method: "POST",
    body: JSON.stringify({ text })
  });
});

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: [],
    isTyping: false,
    pendingExtraction: null,
    error: null
  },
  reducers: {
    pushUserMessage(state, action) {
      state.messages.push({ role: "user", content: action.payload });
    },
    clearPendingExtraction(state) {
      state.pendingExtraction = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.isTyping = true;
        state.error = null;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.isTyping = false;
        state.pendingExtraction = action.payload.extracted_data || null;
        state.messages.push({
          role: "assistant",
          content: action.payload.response,
          action: action.payload.action,
          toolOutput: action.payload.tool_output,
          extractedData: action.payload.extracted_data,
          interactionId: action.payload.interaction_id
        });
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.isTyping = false;
        state.error = action.error.message;
        state.messages.push({ role: "assistant", content: action.error.message });
      })
      .addCase(extractInteraction.fulfilled, (state, action) => {
        state.pendingExtraction = action.payload.extracted_data;
      });
  }
});

export const { clearPendingExtraction, pushUserMessage } = chatSlice.actions;
export default chatSlice.reducer;

