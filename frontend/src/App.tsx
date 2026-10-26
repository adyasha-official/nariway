import { Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import Placeholder from "./pages/Placeholder";
import Brand from "./pages/Brand";
import Navigate from "./pages/Navigate";
import Account from "./pages/Account";
import Report from "./pages/Report";
import SafetyMap from "./pages/SafetyMap";
import Journeys from "./pages/Journeys";
import Shared from "./pages/Shared";
import Settings from "./pages/Settings";
import Admin from "./pages/Admin";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/brand" element={<Brand />} />
      <Route path="/navigate" element={<Navigate />} />
      <Route path="/safety-map" element={<SafetyMap />} />
      <Route path="/report" element={<Report />} />
      <Route path="/journeys" element={<Journeys />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/account" element={<Account />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="/s/:token" element={<Shared />} />
      <Route path="*" element={<Placeholder title="Page not found" note="That page does not exist." />} />
    </Routes>
  );
}
