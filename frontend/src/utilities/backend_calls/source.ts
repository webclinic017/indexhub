export const createSource = async (
  user_id: string,
  source_name: string,
  raw_data_path: string,
  freq: string,
  s3_data_bucket: string,
  time_col: string,
  entity_cols: string[],
  target_cols: string[],
  access_token_indexhub_api: string
) => {
  const create_source_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/sources`;
  const create_source_response = await fetch(create_source_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify({
      user_id: user_id,
      name: source_name,
      raw_data_path: raw_data_path,
      freq: freq,
      s3_data_bucket: s3_data_bucket,
      time_col: time_col,
      entity_cols: entity_cols,
      target_cols: target_cols,
    }),
  });

  const response_json = await create_source_response.json();
  return response_json;
};

export const deleteSource = async (
  access_token_indexhub_api: string,
  source_id: string
) => {
  const delete_source_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/sources?source_id=${source_id}`;
  const delete_source_response = await fetch(delete_source_url, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await delete_source_response.json();
  return response_json;
};

export const getSource = async (
  user_id = "",
  source_id = "",
  access_token_indexhub_api: string
) => {
  let get_source_url = "";

  if (source_id) {
    get_source_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/sources?source_id=${source_id}`;
  } else {
    get_source_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/sources?user_id=${user_id}`;
  }
  const get_source_response = await fetch(get_source_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await get_source_response.json();
  return response_json;
};

export const getSourceColumns = async (
  s3_data_bucket: string,
  raw_source_path: string,
  access_token_indexhub_api: string
) => {
  const get_source_columns_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/sources/columns?s3_data_bucket=${s3_data_bucket}&path=${raw_source_path}`;

  const get_source_columns_response = await fetch(get_source_columns_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await get_source_columns_response.json();

  return response_json;
};
