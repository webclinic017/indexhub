export const getAIRecommendationTable = async (
  page: number,
  display_n: number,
  objective_id: string,
  access_token_indexhub_api: string,
  filter_by: Record<string, any> = {},
  entities_keywords: string[] | null = null
) => {
  const get_ai_recommendation_table_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/tables/${objective_id}/forecast`;

  const get_ai_recommendation_table_response = await fetch(
    get_ai_recommendation_table_url,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access_token_indexhub_api}`,
      },
      body: JSON.stringify({
        filter_by: filter_by,
        entities_keywords: entities_keywords,
        page: page,
        display_n: display_n,
      }),
    }
  );

  const response_json = await get_ai_recommendation_table_response.json();
  return response_json;
};

export const exportAIRecommendationTable = async (
  objective_id: string,
  updated_plans: Record<string, any>[] | null,
  access_token_indexhub_api: string
) => {
  const execute_plan_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/plans/${objective_id}`;

  const execute_plan_response = await fetch(execute_plan_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify({
      updated_plans: updated_plans,
    }),
  });

  const response_json = await execute_plan_response.json();
  return response_json;
};

export const getEntitiesAndInventoryTables = async (
  objective_id: string,
  access_token_indexhub_api: string
) => {
  const get_entities_and_inventory_table_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/inventory/${objective_id}`;

  const get_entities_and_inventory_table_response = await fetch(
    get_entities_and_inventory_table_url,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access_token_indexhub_api}`,
      },
    }
  );

  const response_json = await get_entities_and_inventory_table_response.json();
  return response_json;
};

export const getCombinedEntitiesAndInventoryTable = async (
  objective_id: string,
  entities: Record<string, string[] | string | null>,
  access_token_indexhub_api: string
) => {
  const get_combined_entities_and_inventory_table_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/inventory/table/${objective_id}`;

  const get_combined_entities_and_inventory_table_response = await fetch(
    get_combined_entities_and_inventory_table_url,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access_token_indexhub_api}`,
      },
      body: JSON.stringify({
        forecast_entities: entities["forecast_entities"],
        inventory_entities: entities["inventory_entities"],
      }),
    }
  );

  const response_json =
    await get_combined_entities_and_inventory_table_response.json();
  return response_json;
};

export const getForecastTableView = async (
  objective_id: string,
  access_token_indexhub_api: string
) => {
  const get_forecast_table_view_table_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/tables/${objective_id}/forecast/table_view`;

  const get_forecast_table_view_table_response = await fetch(
    get_forecast_table_view_table_url,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access_token_indexhub_api}`,
      },
      body: JSON.stringify({
        filter_by: {},
      }),
    }
  );

  const response_json = await get_forecast_table_view_table_response.json();
  return response_json;
};

export const getObjectiveEntities = async (
  objective_id: string,
  access_token_indexhub_api: string
) => {
  const get_objective_entities_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/tables/${objective_id}/entities`;

  const get_objective_entities_response = await fetch(
    get_objective_entities_url,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access_token_indexhub_api}`,
      },
    }
  );

  const response_json = await get_objective_entities_response.json();
  return response_json;
};
