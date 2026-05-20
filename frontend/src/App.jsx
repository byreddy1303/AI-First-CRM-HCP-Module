import { useEffect } from "react";
import { useDispatch } from "react-redux";

import LogInteractionPage from "./pages/LogInteractionPage";
import { fetchHcps } from "./redux/hcpSlice";

export default function App() {
  const dispatch = useDispatch();

  // Load HCP list once on startup for form autocomplete
  useEffect(() => {
    dispatch(fetchHcps());
  }, [dispatch]);

  return <LogInteractionPage />;
}
