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