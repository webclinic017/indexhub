export const getTrendChart = async (
    policy_id = "",
    entity_id = "",
    access_token_indexhub_api: string
) => {
    const get_trend_chart_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/charts/trend_chart`;

    const get_trend_chart_response = await fetch(get_trend_chart_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
        body: JSON.stringify({
            policy_id: policy_id,
            entity_id: entity_id,
        })
    });

    const response_json = await get_trend_chart_response.json();
    return response_json;
};