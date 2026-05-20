import { configureStore } from "@reduxjs/toolkit";

import chatReducer from "./chatSlice";
import hcpReducer from "./hcpSlice";
import interactionsReducer from "./interactionsSlice";

export const store = configureStore({
  reducer: {
    chat: chatReducer,
    hcp: hcpReducer,
    interactions: interactionsReducer
  }
});

