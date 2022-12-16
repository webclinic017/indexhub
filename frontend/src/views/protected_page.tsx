import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useAuth0AccessToken } from "../utilities/hooks/auth0"
import { addReportId } from "../actions/actions";
import { AppState } from "../index";
import { useDispatch, useSelector } from "react-redux";


export default function ProtectedPage() {
  const { user, logout } = useAuth0();
  const access_token_indexhub_api = useAuth0AccessToken()
  const dispatch = useDispatch();
  const report_ids = useSelector(
    (state: AppState) => state.reducer?.report_ids
  );

  React.useEffect(() => {
    console.log(report_ids);
  }, [report_ids]);

  const createReport = async () => {
    const create_report_url = `${process.env.REACT_APP_INDEXHUB_API_DOMAIN}/reports`;
    const create_report_response = await fetch(create_report_url, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${access_token_indexhub_api}`,
      },
      body: JSON.stringify({
        "user_id": user?.sub
      })
    });

    const response_json = await create_report_response.json();

    if((Object.prototype.hasOwnProperty.call(response_json, "report_id")) && (Object.prototype.hasOwnProperty.call(response_json, "user_id"))){
      dispatch(addReportId(response_json["report_id"], response_json["user_id"]));
    }
  }

  return (
    <>
      <p>This is a protected page</p>
      <button onClick={() => logout({ returnTo: window.location.origin })}>
        Log Out
      </button>
      <button onClick={() => createReport()}>
        Create Report
      </button>
    </>
  );
}
