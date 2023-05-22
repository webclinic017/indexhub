export const createSource = async (
  user_id: string,
  source_tag: string,
  source_configs: Record<string, any>,
  access_token_indexhub_api: string
) => {
  const create_source_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/sources`;
  const create_source_response = await fetch(create_source_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify({
      user_id: user_id,
      tag: source_tag,
      name: source_configs["source_name"],
      dataset_type: source_configs["dataset_type"],
      conn_fields: JSON.stringify({
        object_path: source_configs["object_path"],
        bucket_name: source_configs["bucket_name"],
        file_ext: source_configs["file_ext"]
      }),
      data_fields: JSON.stringify({
        entity_cols: source_configs["entity_cols"],
        time_col: source_configs["time_col"],
        target_col: source_configs["target_col"],
        feature_cols: source_configs["feature_cols"],
        agg_method: source_configs["agg_method"],
        impute_method: source_configs["impute_method"],
        freq: source_configs["freq"],
        datetime_fmt: source_configs["datetime_fmt"],
        invoice_col: source_configs["invoice_col"],
        price_col: source_configs["price_col"],
        quantity_col: source_configs["quantity_col"],
        product_col: source_configs["product_col"],
      })
    }),
  });

  const response_json = await create_source_response.json();
  return response_json;
};

export const deleteSource = async (
  access_token_indexhub_api: string,
  source_id: string
) => {
  const delete_source_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/sources?source_id=${source_id}`;
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
    get_source_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/sources?source_id=${source_id}`;
  } else {
    get_source_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/sources?user_id=${user_id}`;
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

export const getConnectionsSchema = async (
  user_id: string,
  access_token_indexhub_api: string
) => {
  const get_conn_schema_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/sources/conn-schema/${user_id}`;

  const get_conn_schema_response = await fetch(get_conn_schema_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await get_conn_schema_response.json();

  return response_json;
};

export const getDatasetsSchema = async (
  access_token_indexhub_api: string
) => {
  const get_dataset_schema_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/sources/dataset-schema`;

  const get_dataset_schema_response = await fetch(get_dataset_schema_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await get_dataset_schema_response.json();

  return response_json;
};


export const getS3SourceColumns = async (
  bucket_name: string,
  object_path: string,
  file_ext: string,
  access_token_indexhub_api: string
) => {
  const get_source_columns_url = `${process.env.REACT_APP__FASTAPI__DOMAIN
    }/readers/s3?bucket_name=${bucket_name}&object_path=${object_path}&file_ext=${file_ext}&orient=list`;

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
