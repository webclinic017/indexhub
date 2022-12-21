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
