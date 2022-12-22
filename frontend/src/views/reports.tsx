import React, { useState } from "react";
import { useAuth0AccessToken } from "../utilities/hooks/auth0"
import { AppState } from "../index";
import { useDispatch,useSelector } from "react-redux";
import { createReport, getReport } from "../utilities/backend_calls/report";
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
} from '@chakra-ui/react'

export default function Reports() {
  const access_token_indexhub_api = useAuth0AccessToken()
  const dispatch = useDispatch()
  const [reports, setReports] = useState<{reports: { report_id: string, user_id: string, chart_id: string, table_id: string, status: string, created_at: string }[]}>({reports: []})
  const [current_pagination, setCurrentPagination] = useState(1)

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

  return (
    <VStack padding="10px">
    {reports?.reports.length > 0 && (
      <>
      <TableContainer width="100%" backgroundColor="white" borderRadius="5px">
      <Table variant="striped">
        <Thead backgroundColor="#cbcbcb">
          <Tr>
            <Th>Report ID</Th>
            <Th>Created at</Th>
            <Th>Status</Th>
          </Tr>
        </Thead>
        <Tbody>
          {reports.reports.slice(start_index, start_index + reports_per_page).map((item) => {
            {console.log(reports)}
            return (
              <Tr key={item.report_id}>
                <Td>{item.report_id}</Td>
                <Td>{item.created_at}</Td>
                <Td>{item.status}</Td>
              </Tr>
            )
          })}
        </Tbody>
      </Table>
    </TableContainer>
    <HStack justifyContent="space-between" width="20%">
    <Button onClick={() => setCurrentPagination(current_pagination - 1)} isDisabled={current_pagination == 1}>Prev</Button>
    <>{current_pagination}/{pages_required}</>
    <Button onClick={() => setCurrentPagination(current_pagination + 1)} isDisabled={current_pagination == pages_required}>Next</Button>
    </HStack>
    </>
    )}

    <Button colorScheme="teal" size="sm" onClick={() => createReport(user_details.user_id, access_token_indexhub_api, dispatch)}>
      Create Report
    </Button>
    </VStack>
  );
}
