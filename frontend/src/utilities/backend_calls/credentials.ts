export const createCredentials = async (
  credentials: Record<string, string | number>,
  source_tag: string,
  user_id: string,
  access_token_indexhub_api: string
) => {
  const create_credentials_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/users/${user_id}/credentials`;

  const create_credentials_response = await fetch(create_credentials_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify({
      tag: source_tag,
      secret: credentials,
    }),
  });

  const response_json = await create_credentials_response.json();
  return response_json;
};
