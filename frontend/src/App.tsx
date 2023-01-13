import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ChakraProvider } from "@chakra-ui/react";
import Home from "./views/home";
import Reports from "./views/reports/reports";
import ProtectedRoute from "./utilities/protected_route_handler";
import Layout from "./views/includes/layout";
import themes from "./theme/theme";
import Models from "./views/models";
import Alerts from "./views/alerts";
import Settings from "./views/settings";
import Profile from "./views/profile";
import Docs from "./views/docs";

function App() {
  return (
    <ChakraProvider theme={themes["default_theme"]}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="models" element={<Models />} />
            <Route path="docs" element={<Docs />} />
            {/* All protected pages will go inside this parent route */}
            <Route element={<ProtectedRoute />}>
              <Route path="reports" element={<Reports />} />
              <Route path="alerts" element={<Alerts/>} />
              <Route path="settings" element={<Settings />} />
              <Route path="profile" element={<Profile />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ChakraProvider>
  );
}

export default App;
