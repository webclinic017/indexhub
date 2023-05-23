import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ChakraProvider } from "@chakra-ui/react";
import Home from "./views/home";
import ProtectedRoute from "./utilities/protected_route_handler";
import Layout from "./views/includes/layout";
import { themes } from "./theme/theme";
import Data from "./views/sources/data";
import Alerts from "./views/alerts";
import Settings from "./views/settings";
import Profile from "./views/profile";
import DataAndIntegrations from "./views/sources/data_integrations";
import NewStorage from "./views/storage/new_storage";
import NewObjective from "./views/objectives/new_objective";
import Objectives from "./views/objectives/objectives";
import ObjectivesDashboard from "./views/objectives/objectives_dashboard";
import ForecastObjective from "./views/objectives/forecast/forecast";
import TrendsDashboard from "./views/trends/trends_dashboard";
import Trends from "./views/trends/trends";

function App() {
  return (
    <ChakraProvider theme={themes["default_theme"]}>
      <BrowserRouter>
        <Routes>
          {/* All protected pages will go inside this parent route */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="trends" element={<TrendsDashboard />} />
              <Route path="data" element={<Data />}>
                <Route index element={<DataAndIntegrations />} />
              </Route>
              <Route path="objectives" element={<Objectives />}>
                <Route index element={<ObjectivesDashboard />} />
                <Route path="new_objective" element={<NewObjective />} />
              </Route>
              <Route path="objectives/forecast/:objective_id" element={<ForecastObjective />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="new_storage" element={<NewStorage />} />
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
