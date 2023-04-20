export const getForecastPolicyStats = async (
    policy_id: string,
    access_token_indexhub_api: string
) => {
    const get_forecast_policy_stats_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/stats/${policy_id}`;

    const get_forecast_policy_response = await fetch(get_forecast_policy_stats_url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
    });

    const response_json = await get_forecast_policy_response.json();
    return response_json;
};