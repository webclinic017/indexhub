import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ChakraProvider } from "@chakra-ui/react";
import ProtectedRoute from "./utilities/protected_route_handler";
import Layout from "./views/includes/layout";
import { themes } from "./theme/theme";
import Data from "./views/sources/data";
import Settings from "./views/settings";
import Profile from "./views/profile";
import DataAndIntegrations from "./views/sources/data_integrations";
import NewStorage from "./views/storage/new_storage";
import ObjectivesDashboard from "./views/objectives/objectives_dashboard";
import ForecastObjective from "./views/objectives/forecast/forecast";
import ChatContextProvider from "./views/chat/chat_context";
import NotFound404 from "./views/404";
import ReactErrorBoundary from "./views/includes/error_boundry";
// import TrendsContextProvider from "./views/trends/trends_context";
// import TrendsLanding from "./views/trends/trends_landing";

function App() {
  return (
    <ChakraProvider theme={themes["default_theme"]}>
      <ChatContextProvider>
        <BrowserRouter>
          <ReactErrorBoundary>
            <Routes>
              {/* All protected pages will go inside this parent route */}
              <Route element={<ProtectedRoute />}>
                <Route path="/" element={<Layout />}>
                  {/* <Route
                  index
                  element={
                    <TrendsContextProvider>
                      <TrendsLanding />
                    </TrendsContextProvider>
                  }
                /> */}
                  <Route
                    index
                    element={
                      <ReactErrorBoundary>
                        <ObjectivesDashboard />
                      </ReactErrorBoundary>
                    }
                  />
                  <Route
                    path="data"
                    element={
                      <ReactErrorBoundary>
                        <Data />
                      </ReactErrorBoundary>
                    }
                  >
                    <Route index element={<DataAndIntegrations />} />
                  </Route>

                  {/* <Route path="objectives" element={<Objectives />}>
                  <Route index element={<ObjectivesDashboard />} />
                  <Route path="new_objective" element={<NewObjective />} />
                </Route> */}
                  <Route
                    path="objectives/forecast/:objective_id"
                    element={
                      <ReactErrorBoundary>
                        <ForecastObjective />
                      </ReactErrorBoundary>
                    }
                  />
                  <Route
                    path="new_storage"
                    element={
                      <ReactErrorBoundary>
                        <NewStorage />
                      </ReactErrorBoundary>
                    }
                  />
                  <Route
                    path="settings"
                    element={
                      <ReactErrorBoundary>
                        <Settings />
                      </ReactErrorBoundary>
                    }
                  />
                  <Route
                    path="profile"
                    element={
                      <ReactErrorBoundary>
                        <Profile />
                      </ReactErrorBoundary>
                    }
                  />
                  <Route path="*" element={<NotFound404 />} />
                </Route>
              </Route>
            </Routes>
          </ReactErrorBoundary>
        </BrowserRouter>
      </ChatContextProvider>
    </ChakraProvider>
  );
}

export default App;
