export const getAIRecommendationTable = async (
    page: number,
    display_n: number,
    objective_id: string,
    access_token_indexhub_api: string,
    filter_by: Record<string, any> = {}
) => {
    const get_ai_recommendation_table_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/tables/${objective_id}/forecast`;

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

export const exportAIRecommendationTable = async (
    objective_id: string,
    updated_plans: Record<string, any>[] | null,
    access_token_indexhub_api: string,

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
        })
    });

    const response_json = await execute_plan_response.json();
    return response_json;
};