export const getPoliciesSchema = async (
  user_id: string,
  access_token_indexhub_api: string
) => {
  const get_policy_schema_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/policies/schema/${user_id}`;

  const get_policy_schema_response = await fetch(get_policy_schema_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await get_policy_schema_response.json();

  return response_json;
};

export const createPolicy = async (
  user_id: string,
  policy_configs: Record<string, any>, // eslint-disable-line @typescript-eslint/no-explicit-any
  access_token_indexhub_api: string
) => {
  const create_policy_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/policies`;
  const create_policy_response = await fetch(create_policy_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify({
      user_id: user_id,
      tag: policy_configs["policy_type"],
      name: policy_configs["policy_name"],
      fields: JSON.stringify({
        sources: {
          panel: policy_configs["panel"],
          baseline: policy_configs["baseline"]
            ? policy_configs["baseline"]
            : "",
        },
        direction: policy_configs["direction"],
        risks: policy_configs["risks"],
        target_col: policy_configs["target_col"],
        level_cols: policy_configs["level_cols"],
      }),
    }),
  });

  const response_json = await create_policy_response.json();
  return response_json;
};
