export const getForecastObjectiveStats = async (
    objective_id: string,
    access_token_indexhub_api: string
) => {
    const get_forecast_objective_stats_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/stats/${objective_id}`;

    const get_forecast_objective_response = await fetch(get_forecast_objective_stats_url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
    });

    const response_json = await get_forecast_objective_response.json();
    return response_json;
};