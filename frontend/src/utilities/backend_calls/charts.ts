export const getTrendChart = async (
    objective_id: string,
    chart_tag: string,
    access_token_indexhub_api: string,
    filter_by: Record<string, string[]> = {},
) => {
    const get_trend_chart_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/charts/${objective_id}/${chart_tag}`;
    const get_trend_chart_response = await fetch(get_trend_chart_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
        body: JSON.stringify({
            filter_by: filter_by
        })
    });

    const response_json = await get_trend_chart_response.json();
    return JSON.parse(response_json)
};

export const getSegmentationChart = async (
    objective_id: string,
    chart_tag: string,
    access_token_indexhub_api: string,
    segmentation_factor: string
) => {

    const get_segmentation_chart_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/charts/${objective_id}/${chart_tag}`;
    const get_segmentation_chart_response = await fetch(get_segmentation_chart_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
        body: JSON.stringify({
            segmentation_factor: segmentation_factor
        })
    });

    const response_json = await get_segmentation_chart_response.json();
    return JSON.parse(response_json)
};

export const getRollingForecastChart = async (
    objective_id: string,
    access_token_indexhub_api: string,
) => {

    const get_rolling_forecast_chart_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/charts/${objective_id}/rolling_forecast`;
    const get_rolling_forecast_chart_response = await fetch(get_rolling_forecast_chart_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
        body: JSON.stringify({})
    });

    const response_json = await get_rolling_forecast_chart_response.json();
    return response_json
};

export const getCombinedEntitiesAndInventoryChart = async (
    objective_id: string,
    entities: Record<string, string[] | string | null>,
    access_token_indexhub_api: string,
) => {
    const get_combined_entities_and_inventory_chart_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/inventory/chart/${objective_id}`;

    const get_combined_entities_and_inventory_chart_response = await fetch(get_combined_entities_and_inventory_chart_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
        body: JSON.stringify({
            forecast_entities: entities["forecast_entities"],
            inventory_entity: entities["inventory_entity"]
        })
    });

    const response_json = await get_combined_entities_and_inventory_chart_response.json();
    return JSON.parse(response_json)
};