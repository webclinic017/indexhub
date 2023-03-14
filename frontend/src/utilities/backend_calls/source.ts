export const createSource = async (
  user_id: string,
  source_name: string,
  freq: string,
  time_col: string,
  entity_cols: string[],
  feature_cols: string[],
  source_type: string,
  source_configs: Record<string, string>,
  datetime_fmt: string,
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
      tag: source_type,
      name: source_name,
      variables: JSON.stringify(source_configs),
      freq: freq,
      datetime_fmt: datetime_fmt,
      entity_cols: entity_cols,
      time_col: time_col,
      feature_cols: feature_cols,
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

export const getSourcesSchema = async (
  user_id: string,
  access_token_indexhub_api: string
) => {
  const get_sources_schema_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/sources/schema/${user_id}`;

  const get_sources_schema_response = await fetch(get_sources_schema_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await get_sources_schema_response.json();

  return response_json;
};

export const getS3SourceColumns = async (
  s3_bucket: string,
  s3_path: string,
  file_ext: string,
  access_token_indexhub_api: string
) => {
  const get_source_columns_url = `${
    process.env.REACT_APP_INDEXHUB_API_DOMAIN
  }/readers/s3?s3_bucket=${s3_bucket}&s3_path=${s3_path}&file_ext=${file_ext}&orient=list&n_rows=${1}`;

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
