import { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";

export const useAuth0AccessToken = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [auth0_access_token, setAuth0AccessToken] = useState("");

  useEffect(() => {
    const getAccessToken = async () => {
      try {
        const access_token = await getAccessTokenSilently({
          audience: process.env.REACT_APP__AUTH0_M2M__AUDIENCE!, // eslint-disable-line @typescript-eslint/no-non-null-assertion
        });
        setAuth0AccessToken(access_token);
      } catch (e: any) {
        console.log(e.message);
      }
    };

    getAccessToken();
  }, []);

  return auth0_access_token;
};
