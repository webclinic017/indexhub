import React from "react";
import { useAuth0AccessToken } from "../utilities/hooks/auth0"
import { AppState } from "../index";
import { useDispatch,useSelector } from "react-redux";
import { createReport } from "../utilities/backend_calls/report";
import { Button, Container } from '@chakra-ui/react'

export default function Reports() {
  const access_token_indexhub_api = useAuth0AccessToken()
  const dispatch = useDispatch()
  const report_ids = useSelector(
    (state: AppState) => state.reducer?.report_ids
  );
  const user_details = useSelector(
    (state: AppState) => state.reducer?.user
  );

  React.useEffect(() => {
    console.log(report_ids);
  }, [report_ids]);

  React.useEffect(() => {
    console.log(user_details)
  }, [user_details])

  return (
    <Container display="flex" justifyContent="center" padding="10px">
      <Button colorScheme="teal" size="sm" onClick={() => createReport(user_details.user_id, access_token_indexhub_api, dispatch)}>
        Create Report
      </Button>
    </Container>
  );
}
