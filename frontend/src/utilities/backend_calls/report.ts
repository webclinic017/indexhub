import { addReportId } from "../../actions/actions";

export const createReport = async (user_id: string, source_name: string, level_cols: string[], target_col: string, source_id: string, access_token_indexhub_api:string) => {
    const create_report_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/reports`;
    const create_report_response = await fetch(create_report_url, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${access_token_indexhub_api}`,
      },
      body: JSON.stringify({
        "user_id": user_id,
        "source_name": source_name,
        "level_cols": level_cols,
        "target_col": target_col,
        "source_id": source_id
      })
    });

    const response_json = await create_report_response.json();

    return response_json
  }

export const deleteReport = async (access_token_indexhub_api:string, report_id: string) => {
  const delete_report_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/reports?report_id=${report_id}`;
  const delete_report_response = await fetch(delete_report_url, {
    method: "DELETE",
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
  });

  const response_json = await delete_report_response.json();
  return response_json
}

export const getReport = async (user_id = "", report_id = "", access_token_indexhub_api:string) => {
  let get_report_url = ""

  if (report_id) {
    get_report_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/reports?report_id=${report_id}`;
  } else {
    get_report_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/reports?user_id=${user_id}`
  }
  const get_report_response = await fetch(get_report_url, {
    method: "GET",
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },

  });

  const response_json = await get_report_response.json();
  return response_json
}

export const getChart = async (report_id:string, tag: string, access_token_indexhub_api:string, filters: any) => {
  let get_chart_url = ""

  get_chart_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/charts?report_id=${report_id}&tag=${tag}`;

  const get_chart_response = await fetch(get_chart_url, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify(filters)
  });

  const response_json = await get_chart_response.json();
  return response_json
}

export const getTable = async (report_id:string, tag: string, access_token_indexhub_api:string, filters: any = {}) => {
  let get_table_url = ""

  get_table_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/tables?report_id=${report_id}&tag=${tag}`;

  const get_chart_response = await fetch(get_table_url, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },
    body: JSON.stringify(filters)
  });

  const response_json = await get_chart_response.json();
  return response_json
}

export const getSourceProfilingHtml = async (source_id: string, access_token_indexhub_api:string) => {
 
  const get_source_profiling_html_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/reports/profiling?source_id=${source_id}`;
  
  const get_report_response = await fetch(get_source_profiling_html_url, {
    method: "GET",
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },

  });

  const response_json = await get_report_response.json();
  return response_json
}

export const getLevelsData = async (report_id = "", access_token_indexhub_api:string) => {
  const get_levels_data_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/reports/levels?report_id=${report_id}`;
  
  const get_levels_data_response = await fetch(get_levels_data_url, {
    method: "GET",
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${access_token_indexhub_api}`,
    },

  });

  const response_json = await get_levels_data_response.json();
  return response_json
}