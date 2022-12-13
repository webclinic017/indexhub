import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ChakraProvider } from "@chakra-ui/react";
import Home from "./views/home";
import NestedPage from "./views/nested_page/nested_page";
import NestedView from "./views/nested_page/nested_view";
import ProtectedPage from "./views/protected_page";
import Login from "./views/login";
import ProtectedNestedView from "./views/nested_page/protected_nested_view";
import ProtectedRoute from "./utilities/protected_route_handler";
import Layout from "./views/includes/layout";
import themes from "./theme/theme";

function App() {
  return (
    <ChakraProvider theme={themes["default_theme"]}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="nested_page" element={<NestedPage />}>
              <Route path="nested_view" element={<NestedView />} />
              <Route
                path="protected_nested_view"
                element={
                  <ProtectedRoute nested_view={true}>
                    <ProtectedNestedView />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* All protected pages will go inside this parent route */}
            <Route element={<ProtectedRoute />}>
              <Route path="protected_page" element={<ProtectedPage />} />
            </Route>

            <Route path="/login" element={<Login />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ChakraProvider>
  );
}

export default App;
