import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { apiRequest } from "./api";

export const fetchHcps = createAsyncThunk("hcp/fetchAll", async (query = "") => {
  const qs = query ? `?q=${encodeURIComponent(query)}` : "";
  return apiRequest(`/api/hcp${qs}`);
});

const hcpSlice = createSlice({
  name: "hcp",
  initialState: {
    hcpList: [],
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.loading = false;
        state.hcpList = action.payload;
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export default hcpSlice.reducer;
