export const getAllIntegrations = async (
    access_token_indexhub_api: string
) => {
    const get_all_integrations_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/integrations/all`;

    const get_all_integrations_response = await fetch(get_all_integrations_url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
    });

    const response_json = await get_all_integrations_response.json();
    return response_json;
};

export const getUserIntegrations = async (
    user_id: string,
    access_token_indexhub_api: string
) => {
    const get_user_credentials_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/integrations/${user_id}`;

    const get_user_credentials_response = await fetch(get_user_credentials_url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
    });

    const response_json = await get_user_credentials_response.json();
    return response_json;

};

export const setUserIntegrations = async (
    user_id: string,
    user_integration_ids: number[],
    access_token_indexhub_api: string
) => {
    const set_user_integrations_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/integrations/${user_id}`;

    const set_user_integrations_response = await fetch(set_user_integrations_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${access_token_indexhub_api}`,
        },
        body: JSON.stringify({
            user_integrations: user_integration_ids,
        }),
    });

    const response_json = await set_user_integrations_response.json();
    return response_json;
}
