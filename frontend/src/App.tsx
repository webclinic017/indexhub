import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ChakraProvider } from "@chakra-ui/react";
import Home from "./views/home";
import Reports from "./views/reports/reports";
import ProtectedRoute from "./utilities/protected_route_handler";
import Layout from "./views/includes/layout";
import { themes } from "./theme/theme";
import Data from "./views/sources/data";
import Alerts from "./views/alerts";
import Settings from "./views/settings";
import Profile from "./views/profile";
import Docs from "./views/docs";
import Forecast_Recommendations from "./views/reports/report_types/forecast_prediction";
import NewSource from "./views/sources/new_source";
import DataAndIntegrations from "./views/sources/data_integrations";
import SourceProfiling from "./views/reports/profiling";
import NewStorage from "./views/storage/new_storage";
import NewObjective from "./views/objectives/new_objective";
import Objectives from "./views/objectives/objectives";
import ObjectivesDashboard from "./views/objectives/objectives_dashboard";
import ForecastObjective from "./views/objectives/forecast/forecast";
import Dashboard from "./views/dashboard";

function App() {
  return (
    <ChakraProvider theme={themes["default_theme"]}>
      <BrowserRouter>
        <Routes>
          {/* All protected pages will go inside this parent route */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="docs" element={<Docs />} />
              <Route path="data" element={<Data />}>
                <Route index element={<DataAndIntegrations />} />
                {/* <Route path="new_source" element={<NewSource />} /> */}
              </Route>
              <Route path="objectives" element={<Objectives />}>
                <Route index element={<ObjectivesDashboard />} />
                <Route path="new_objective" element={<NewObjective />} />
              </Route>
              <Route path="objectives/forecast/:objective_id" element={<ForecastObjective />} />
              <Route path="reports" element={<Reports />} />
              <Route
                path="reports/profiling/:source_id"
                element={<SourceProfiling />}
              />
              <Route
                path="reports/:id"
                element={<Forecast_Recommendations />}
              />
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
