import React from "react";
import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { useAuth0AccessToken } from "./hooks/auth0";
import { useDispatch } from "react-redux";
import { initUser } from "../actions/actions";


const getUserDetails = async (user_id: string, access_token: string) => {
  const get_user_details_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/users/${user_id}`;
  const get_user_details_response = await fetch(get_user_details_url, {
    method: "GET",
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token}`,
    },
  });
  return get_user_details_response
}

const createUser = async (user: any, access_token: string) => {
  const create_user_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/user`;
  const create_user_response = await fetch(create_user_url, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token}`,
    },
    body: JSON.stringify({
      "user_id": user?.sub,
      "nickname": user?.nickname,
      "name": user?.name,
      "email": user?.email,
      "email_verified": user?.email_verified
    })
  });

  return create_user_response
}

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

  useEffect(() => {
    if (isAuthenticated) {
      getUserDetails(user?.sub!, access_token_indexhub_api).then(async (response)=> { // eslint-disable-line @typescript-eslint/no-non-null-asserted-optional-chain
        const status = await response.status
        if (status == 400){
          createUser(user, access_token_indexhub_api).then(async (response)=> { // eslint-disable-line @typescript-eslint/no-non-null-asserted-optional-chain
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
