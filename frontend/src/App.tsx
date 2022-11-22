import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ChakraProvider } from "@chakra-ui/react";
import { useDispatch, useSelector } from "react-redux";
import { loadComingSoon } from "./actions/actions";
import { AppState } from "./index";
import Home from "./views/home";
import NestedPage from "./views/nested_page/nested_page";
import NestedView from "./views/nested_page/nested_view";
import ProtectedPage from "./views/protected_page";
import Login from "./views/login";
import ProtectedNestedView from "./views/nested_page/protected_nested_view";
import ProtectedRoute from "./utilities/protected_route_handler";
import Layout from "./views/includes/layout";

function App() {
  const dispatch = useDispatch();
  const coming_soon = useSelector(
    (state: AppState) => state.reducer?.coming_soon
  );

  React.useEffect(() => {
    dispatch(loadComingSoon());
  }, []);

  React.useEffect(() => {
    console.log(coming_soon);
  }, [coming_soon]);

  return (
    <ChakraProvider>
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
