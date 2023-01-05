import { addReportId } from "../../actions/actions";

export const createReport = async (user_id: string, access_token_indexhub_api:string, dispatch: any) => {
    const create_report_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/reports`;
    const create_report_response = await fetch(create_report_url, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${access_token_indexhub_api}`,
      },
      body: JSON.stringify({
        "user_id": user_id
      })
    });

    const response_json = await create_report_response.json();

    if((Object.prototype.hasOwnProperty.call(response_json, "report_id")) && (Object.prototype.hasOwnProperty.call(response_json, "user_id"))){
      dispatch(addReportId(response_json["report_id"], response_json["user_id"]));
    }
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

export const getChart = async (chart_id:string, access_token_indexhub_api:string, filters: any) => {
  let get_chart_url = ""

  get_chart_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/chart?chart_id=${chart_id}`;

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

export const getTable = async (table_id:string, access_token_indexhub_api:string, filters: any = {}) => {
  let get_table_url = ""

  get_table_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/table?table_id=${table_id}`;

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
