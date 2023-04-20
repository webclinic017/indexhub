export const getAIRecommendationTable = async (
    page: number,
    display_n: number,
    policy_id: string,
    access_token_indexhub_api: string,
    filter_by: Record<string, any> = {}
) => {
    const get_ai_recommendation_table_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/tables/${policy_id}/forecast`;

    const get_ai_recommendation_table_response = await fetch(get_ai_recommendation_table_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
        body: JSON.stringify({
            filter_by: filter_by,
            page: page,
            display_n: display_n
        })
    });

    const response_json = await get_ai_recommendation_table_response.json();
    return response_json;
};