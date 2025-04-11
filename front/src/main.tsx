import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { BrowserRouter ,Route,Routes} from "react-router";
import HireMate from "./compo/one.tsx";
import HireMateResult from "./compo/two.tsx";
createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <StrictMode>
    <Routes>
      <Route path="/" element={<HireMate />} />
      <Route path="/candidates" element={<HireMateResult />} />
    </Routes>
    </StrictMode>
  </BrowserRouter>
);
