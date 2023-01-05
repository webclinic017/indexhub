import React, { useState } from "react";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0"
import { AppState } from "../../index";
import { useDispatch,useSelector } from "react-redux";
import { createReport, getReport} from "../../utilities/backend_calls/report";
import {
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  VStack,
  HStack,
  Container,
} from "@chakra-ui/react"
import Forecast_Recommendations from "./report_types/forecast_prediction";

export type Report = {
  report_id: string,
  user_id: string,
  chart_id: string,
  table_id: string,
  status: string,
  created_at: string
  filters: Record<string, any>
}

const getStatusColor = (status: string) => {
  switch(status){
    case "COMPLETE": {
      return "#00be00"
    }
    case "RUNNING": {
      return "#8c918c"
    }
    case "ERROR": {
      return "#ff4444"
    }
  }
}

export default function Reports() {
  const access_token_indexhub_api = useAuth0AccessToken()
  const dispatch = useDispatch()
  const [reports, setReports] = useState<{reports: Report[]}>({reports: []})
  const [current_pagination, setCurrentPagination] = useState(1)
  const [selectedReport, setSelectedReport] = useState<Report>({report_id: "", user_id: "", chart_id: "", table_id: "", status: "", created_at: "", filters: {}});

  const clearSelectedReport = () => {
    setSelectedReport({report_id: "", user_id: "", chart_id: "", table_id: "", status: "", created_at: "", filters: {}})
  }

  const report_ids = useSelector(
    (state: AppState) => state.reducer?.report_ids
  );
  const user_details = useSelector(
    (state: AppState) => state.reducer?.user
  );

  const reports_per_page = 12
  const start_index = (current_pagination - 1) * reports_per_page
  const pages_required = Math.ceil(reports.reports.length/reports_per_page)

  React.useEffect(() => {
    const getReportByUserId = async () => {
      const reports_response = await getReport(user_details.user_id, "", access_token_indexhub_api)
      setReports(reports_response)
    }
    if (access_token_indexhub_api && user_details.user_id) {
      getReportByUserId()
    }
  }, [user_details, access_token_indexhub_api, report_ids])

  if (selectedReport.report_id) {
    return (
      <Forecast_Recommendations selectedReport={selectedReport} access_token_indexhub_api={access_token_indexhub_api} clearSelectedReport={clearSelectedReport}/>
    )
  } else {
    return (
      <VStack padding="10px">
        {reports?.reports.length > 0 && (
          <>
            <VStack backgroundColor="white" width="100%" borderRadius="8px" box-shadow="0px 0px 1px rgba(48, 49, 51, 0.05),0px 2px 4px rgba(48, 49, 51, 0.1)">
              <HStack padding="20px" width="100%" alignItems="flex-start"><p>Reports</p></HStack>
              <TableContainer width="100%" backgroundColor="white">
                <Table>
                  <Thead backgroundColor="#f7fafc">
                    <Tr borderTop="1px solid #E2E8F0">
                      <Th>Report ID</Th>
                      <Th>Created at</Th>
                      <Th width="200px" textAlign="center">Status</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {reports.reports.slice(start_index, start_index + reports_per_page).map((item) => {
                      return (
                        <Tr height="73px" onClick={() => setSelectedReport(item)} key={item.report_id}>
                          <Td>{item.report_id}</Td>
                          <Td>{item.created_at}</Td>
                          <Td><Container display="flex" justifyContent="center" padding="5px" backgroundColor={getStatusColor(item.status)} borderRadius="5px">{item.status}</Container></Td>
                        </Tr>
                      )
                    })}
                  </Tbody>
                </Table>
              </TableContainer>
              <HStack padding="0 25px" marginTop="20px !important" marginBottom="20px !important" justifyContent="space-between" width="100%">
                <p>Showing {current_pagination} of {pages_required} pages</p>
                <HStack>
                  <Button onClick={() => setCurrentPagination(current_pagination - 1)} isDisabled={current_pagination == 1}>Previous</Button>
                  <Button onClick={() => setCurrentPagination(current_pagination + 1)} isDisabled={current_pagination == pages_required}>Next</Button>
                </HStack>
              </HStack>
            </VStack>
          </>
        )}

        <Button colorScheme="teal" size="sm" onClick={() => createReport(user_details.user_id, access_token_indexhub_api, dispatch)}>
          Create Report
        </Button>
      </VStack>
    )
  }
}
