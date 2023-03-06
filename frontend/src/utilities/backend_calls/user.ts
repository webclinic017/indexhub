import { User } from "@auth0/auth0-react";

export const getUserDetails = async (user_id: string, access_token: string) => {
  const get_user_details_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/users/${user_id}`;
  const get_user_details_response = await fetch(get_user_details_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token}`,
    },
  });
  return get_user_details_response;
};

export const createUser = async (
  user: User | undefined,
  access_token: string
) => {
  const create_user_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/users`;
  const create_user_response = await fetch(create_user_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token}`,
    },
    body: JSON.stringify({
      user_id: user?.sub,
      nickname: user?.nickname,
      name: user?.name,
      email: user?.email,
      email_verified: user?.email_verified,
    }),
  });

  return create_user_response;
};
