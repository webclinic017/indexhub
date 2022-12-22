import React from "react";
import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { useAuth0AccessToken } from "./hooks/auth0";
import { useDispatch } from "react-redux";
import { initUser } from "../actions/actions";
import { getUserDetails, createUser } from "./backend_calls/user";
import { Button } from "@chakra-ui/react";
import { useLocation } from 'react-router-dom';

export default function ProtectedRoute({
  children,
  nested_view,
}: {
  children?: JSX.Element;
  nested_view?: boolean;
}): JSX.Element {
  const {user, isAuthenticated, isLoading, loginWithRedirect } = useAuth0();
  const access_token_indexhub_api = useAuth0AccessToken()
  const dispatch = useDispatch()
  const current_path = useLocation().pathname

  useEffect(() => {
    if (isAuthenticated && access_token_indexhub_api) {
      getUserDetails(user?.sub!, access_token_indexhub_api).then(async (response)=> { // eslint-disable-line @typescript-eslint/no-non-null-asserted-optional-chain
        const status = await response.status
        if (status == 400){
          createUser(user, access_token_indexhub_api).then(async ()=> { // eslint-disable-line @typescript-eslint/no-non-null-asserted-optional-chain
            getUserDetails(user?.sub!, access_token_indexhub_api).then(async (response)=> { // eslint-disable-line @typescript-eslint/no-non-null-asserted-optional-chain
              const user_details = await response.json()
              dispatch(initUser(user_details));
            })
          })
        } else if(status == 200) {
          const user_details = await response.json()
          dispatch(initUser(user_details));
        }
        else {
          window.alert("There was an issue in retrieving your user info. Please try logging in again later")
        }
      })
    }
  }, [access_token_indexhub_api])

  // Handle either redirection to login page or showing a login button to redirect to login page here
  if (!isLoading) {
    if (!isAuthenticated) {
      if (nested_view) {
        return (
          <Button colorScheme="teal" size="sm" onClick={() => loginWithRedirect({
            redirectUri: `http://localhost:3000${current_path}`
          })}>
            Login
          </Button>
        )
      } else {
        loginWithRedirect({
          redirectUri: `http://localhost:3000${current_path}`
        })
      }
    } else {
      return children ? children : <Outlet />;
    }
  }
  return <></>;
}
