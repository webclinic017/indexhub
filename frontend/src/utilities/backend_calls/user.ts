import { User } from "@auth0/auth0-react";

export const getUserDetails = async (user_id: string, access_token: string) => {
  const get_user_details_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/users/${user_id}`;
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
  const create_user_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/users`;
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

export const getStorageSchema = async (access_token: string) => {
  const get_storage_schema_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/users/schema/storage`;
  const get_storage_schema_response = await fetch(get_storage_schema_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token}`,
    },
  });

  const response_json = await get_storage_schema_response.json();

  return response_json;
};

export const createStorage = async (
  storage_credentials: Record<string, string | number>,
  storage_bucket_name: string,
  storage_tag: string,
  user_id: string,
  access_token_indexhub_api: string
) => {
  const create_storage_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/users/${user_id}/storage`;

  const create_credentials_response = await fetch(create_storage_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify({
      tag: storage_tag,
      secret: storage_credentials,
      storage_bucket_name: storage_bucket_name,
    }),
  });

  const response_json = await create_credentials_response.json();
  return response_json;
};
