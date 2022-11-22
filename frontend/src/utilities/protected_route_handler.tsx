import React from "react";
import { Outlet } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";

export default function ProtectedRoute({
  children,
  nested_view,
}: {
  children?: JSX.Element;
  nested_view?: boolean;
}): JSX.Element {
  const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();

  console.log(isAuthenticated);
  // Handle either redirection to login page or showing a login button to redirect to login page here
  if (!isLoading) {
    if (!isAuthenticated) {
      if (nested_view) {
        return <p>Show login button here</p>;
      } else {
        loginWithRedirect();
      }
    } else {
      return children ? children : <Outlet />;
    }
  }
  return <></>;
}
