import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ChakraProvider } from "@chakra-ui/react";
import Home from "./views/home";
import Reports from "./views/reports/reports";
import ProtectedRoute from "./utilities/protected_route_handler";
import Layout from "./views/includes/layout";
import { themes } from "./theme/theme";
import Sources from "./views/sources/sources";
import Alerts from "./views/alerts";
import Settings from "./views/settings";
import Profile from "./views/profile";
import Docs from "./views/docs";
import Forecast_Recommendations from "./views/reports/report_types/forecast_prediction";
import NewSource from "./views/sources/new_source";
import SourcesTable from "./views/sources/sources_table";
import SourceProfiling from "./views/reports/profiling";
import NewStorage from "./views/storage/new_storage";
import NewPolicy from "./views/policies/new_policy";
import Policies from "./views/policies/policies";
import PoliciesDashboard from "./views/policies/policies_dashboard";
import PolicyForecast from "./views/policies/forecast/forecast";

function App() {
  return (
    <ChakraProvider theme={themes["default_theme"]}>
      <BrowserRouter>
        <Routes>
          {/* All protected pages will go inside this parent route */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="docs" element={<Docs />} />
              <Route path="sources" element={<Sources />}>
                <Route index element={<SourcesTable />} />
                <Route path="new_source" element={<NewSource />} />
              </Route>
              <Route path="policies" element={<Policies />}>
                <Route index element={<PoliciesDashboard />} />
                <Route path="new_policy" element={<NewPolicy />} />
              </Route>
              <Route path="policies/forecast/:policy_id" element={<PolicyForecast />}/>
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
