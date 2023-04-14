const dummy_data = [
    {
        "title": "trips_in_000s to date",
        "subtitle": "Last 3 months",
        "values": {
            "sum": 15632.43
        }
    },
    {
        "title": "AI Predicted (Forecast)",
        "subtitle": "Next 3 months",
        "values": {
            "sum": 14787.19,
            "diff": -845.25,
            "pct_change": -5.41
        }
    },
    {
        "title": "AI Uplift",
        "subtitle": "Backtest results over the last 5 months",
        "values": {
            "sum": -1576.67,
            "mean_pct": -0.31
        }
    }
]

export const getForecastPolicyStats = async (

) => {
    // const get_trend_chart_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/charts/trend_chart`;

    // const get_trend_chart_response = await fetch(get_trend_chart_url, {
    //     method: "POST",
    //     headers: {
    //         "Content-Type": "application/json",
    //         Authorization: `Bearer ${access_token_indexhub_api}`,
    //     },
    //     body: JSON.stringify({
    //         policy_id: policy_id,
    //         entity_id: entity_id,
    //     })
    // });

    // const response_json = await get_trend_chart_response.json();
    // return response_json;
    return dummy_data
};