import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { apiRequest } from "./api";
import { sendChatMessage } from "./chatSlice";

export const createInteraction = createAsyncThunk("interactions/create", async (payload) => {
  return apiRequest("/api/interactions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
});

export const updateInteraction = createAsyncThunk(
  "interactions/update",
  async ({ interactionId, updates }) => {
    return apiRequest(`/api/interactions/${interactionId}`, {
      method: "PUT",
      body: JSON.stringify(updates)
    });
  }
);

export const deleteInteraction = createAsyncThunk(
  "interactions/delete",
  async (interactionId) => {
    await apiRequest(`/api/interactions/${interactionId}`, { method: "DELETE" });
    return interactionId;
  }
);

export const deleteAllInteractions = createAsyncThunk(
  "interactions/deleteAll",
  async () => {
    const result = await apiRequest("/api/interactions", { method: "DELETE" });
    return result?.deleted ?? 0;
  }
);

const interactionsSlice = createSlice({
  name: "interactions",
  initialState: {
    list: [],
    current: null,
    loading: false,
    error: null,
    deletedIds: []
  },
  reducers: {
    clearInteractionError(state) {
      state.error = null;
    },
    // Used to sync state after agent-initiated deletes (no API call needed)
    purgeOne(state, action) {
      const id = action.payload;
      state.list = state.list.filter((row) => row.id !== id);
      state.deletedIds.push(id);
      if (state.current?.id === id) state.current = null;
    },
    purgeAll(state) {
      const ids = state.list.map((row) => row.id);
      state.deletedIds.push(...ids);
      state.list = [];
      state.current = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(createInteraction.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.loading = false;
        state.current = action.payload;
        state.list.unshift(action.payload);
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        state.current = action.payload;
        state.list = state.list.map((row) => (row.id === action.payload.id ? action.payload : row));
      })
      .addCase(deleteInteraction.fulfilled, (state, action) => {
        state.list = state.list.filter((row) => row.id !== action.payload);
        state.deletedIds.push(action.payload);
        if (state.current?.id === action.payload) state.current = null;
      })
      .addCase(deleteAllInteractions.fulfilled, (state) => {
        const ids = state.list.map((row) => row.id);
        state.deletedIds.push(...ids);
        state.list = [];
        state.current = null;
      })
      // Clear the stale "Saved interaction" banner whenever any non-log chat action completes
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        if (action.payload.action !== "log") {
          state.current = null;
        }
      });
  }
});

export const { clearInteractionError, purgeOne, purgeAll } = interactionsSlice.actions;
export default interactionsSlice.reducer;

