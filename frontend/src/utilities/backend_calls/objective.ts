export const getObjectivesSchema = async (
  user_id: string,
  access_token_indexhub_api: string
) => {
  const get_objective_schema_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/objectives/schema/${user_id}`;

  const get_objective_schema_response = await fetch(get_objective_schema_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await get_objective_schema_response.json();

  return response_json;
};

export const createObjective = async (
  user_id: string,
  objective_configs: Record<string, any>,
  access_token_indexhub_api: string
) => {
  const create_objective_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/objectives`;
  const create_objective_response = await fetch(create_objective_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify({
      user_id: user_id,
      tag: objective_configs["objective_type"],
      name: objective_configs["objective_name"],
      sources: JSON.stringify({
        panel: objective_configs["panel"],
        panel_name: objective_configs["panel_name"],
        baseline: objective_configs["baseline"]
          ? objective_configs["baseline"]
          : "",
        baseline_name: objective_configs["baseline_name"]
          ? objective_configs["baseline_name"]
          : "",
        inventory: objective_configs["inventory"]
          ? objective_configs["inventory"]
          : "",
        inventory_name: objective_configs["inventory_name"]
          ? objective_configs["inventory_name"]
          : "",
        transaction: objective_configs["transaction"]
          ? objective_configs["transaction"]
          : "",
        transaction_name: objective_configs["transaction_name"]
          ? objective_configs["transaction_name"]
          : "",
      }),
      fields: JSON.stringify({
        direction: objective_configs["direction"],
        risks: objective_configs["risks"],
        target_col: objective_configs["target_col"],
        level_cols: objective_configs["level_cols"],
        description: objective_configs["objective_description"],
        agg_method: objective_configs["agg_method"],
        impute_method: objective_configs["impute_method"],
        error_type: objective_configs["error_type"],
        fh: objective_configs["fh"],
        freq: objective_configs["freq"],
        goal: objective_configs["goal"],
        holiday_regions: objective_configs["holiday_regions"],
        max_lags: objective_configs["max_lags"],
        min_lags: objective_configs["min_lags"],
        baseline_model: objective_configs["baseline_model"],
        n_splits: objective_configs["n_splits"],
        invoice_col: objective_configs["invoice_col"]
          ? objective_configs["invoice_col"]
          : "",
        product_col: objective_configs["product_col"]
          ? objective_configs["product_col"]
          : "",
      }),
    }),
  });

  const response_json = await create_objective_response.json();
  return response_json;
};

export const getObjective = async (
  user_id = "",
  objective_id = "",
  access_token_indexhub_api: string
) => {
  let get_objective_url = "";

  if (objective_id) {
    get_objective_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/objectives/${objective_id}`;
  } else {
    get_objective_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/objectives?user_id=${user_id}`;
  }
  const get_objective_response = await fetch(get_objective_url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await get_objective_response.json();
  return response_json;
};
