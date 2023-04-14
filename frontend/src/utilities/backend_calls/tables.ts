const dummy_data = [
    {
        "state": "West Australia",
        "table": [
            {
                "time_col": '2019-03-01T00:00:00',
                "Forecast Period": 1,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            },
            {
                "time_col": '2019-03-02T00:00:00',
                "Forecast Period": 2,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            },
            {
                "time_col": '2019-03-03T00:00:00',
                "Forecast Period": 3,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            }
        ]
    },
    {
        "state": "Adelaide",
        "table": [
            {
                "time_col": '2019-03-01T00:00:00',
                "Forecast Period": 1,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            },
            {
                "time_col": '2019-03-02T00:00:00',
                "Forecast Period": 2,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            },
            {
                "time_col": '2019-03-03T00:00:00',
                "Forecast Period": 3,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            }
        ]
    },
    {
        "state": "Canberra",
        "table": [
            {
                "time_col": '2019-03-01T00:00:00',
                "Forecast Period": 1,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            },
            {
                "time_col": '2019-03-02T00:00:00',
                "Forecast Period": 2,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            },
            {
                "time_col": '2019-03-03T00:00:00',
                "Forecast Period": 3,
                "Baseline": 493.8525085449219,
                "Forecast": 423.5927151720318,
                "Forecast (10% quantile)": 712.488031617323,
                "Forecast (90% quantile)": 835.1494279914596,
                "Override": null
            }
        ]
    }
]

// const dummy_data = {
//     "table_data": {
//         "Adelaide": [
//             {
//                 "date": '2019-03-01T00:00:00',
//                 "forecast_horizon": 1,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//             {
//                 "date": '2019-03-02T00:00:00',
//                 "forecast_horizon": 2,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//             {
//                 "date": '2019-03-03T00:00:00',
//                 "forecast_horizon": 3,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//         ],
//         "Brisbane & Gold Coast": [
//             {
//                 "date": '2019-03-01T00:00:00',
//                 "forecast_horizon": 1,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//             {
//                 "date": '2019-03-02T00:00:00',
//                 "forecast_horizon": 2,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//             {
//                 "date": '2019-03-03T00:00:00',
//                 "forecast_horizon": 3,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//         ],
//         "Canberra": [
//             {
//                 "date": '2019-03-01T00:00:00',
//                 "forecast_horizon": 1,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//             {
//                 "date": '2019-03-02T00:00:00',
//                 "forecast_horizon": 2,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//             {
//                 "date": '2019-03-03T00:00:00',
//                 "forecast_horizon": 3,
//                 "benchmark": 100,
//                 "ai_forecast": 101,
//                 "ai_forecast_90": 90,
//                 "ai_forecast_10": 110,
//                 "override": null
//             },
//         ],
//     },
//     "sum_ai_forecasts": 909,
//     "sum_actual": 506,
//     "readable_names": {
//         "date": "Date",
//         "forecast_horizon": "Forecast Horizon",
//         "benchmark": "Benchmark",
//         "ai_forecast": "AI Forecast",
//         "ai_forecast_90": "90% Forecast",
//         "ai_forecast_10": "10% Forecast",
//         "override": "Override"
//     }
// }

export const getAIRecommendationTable = async (

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