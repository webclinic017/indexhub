import React, { useState } from "react";
import { useAuth0AccessToken } from "../utilities/hooks/auth0"
import { AppState } from "../index";
import { useDispatch,useSelector } from "react-redux";
import { createReport, getChart, getReport } from "../utilities/backend_calls/report";
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
} from "@chakra-ui/react"
import ReactEcharts from "echarts-for-react"

export default function Reports() {
  const access_token_indexhub_api = useAuth0AccessToken()
  const dispatch = useDispatch()
  const [reports, setReports] = useState<{reports: { report_id: string, user_id: string, chart_id: string, table_id: string, status: string, created_at: string }[]}>({reports: []})
  const [current_pagination, setCurrentPagination] = useState(1)
  const [selectedReport, setSelectedReport] = useState<{report_id: string, user_id: string, chart_id: string, table_id: string, status: string, created_at: string}>({report_id: "", user_id: "", chart_id: "", table_id: "", status: "", created_at: ""});
  const [chartData, setChartData] = useState<{chart_id: string, title : string, chart_type: string, readable_names: Record<string, never>, entity_id: string, chart_data: Record<string, never>}>({chart_id: "", title : "", chart_type: "", readable_names: {}, entity_id: "", chart_data: {}});
  const clearSelectedReport = () => {
    setSelectedReport({report_id: "", user_id: "", chart_id: "", table_id: "", status: "", created_at: ""})
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

  React.useEffect(() => {
    const getChartByChartId = async () => {
      const chart_response = await getChart(selectedReport?.chart_id, access_token_indexhub_api)
      setChartData(chart_response)
    }
    if (access_token_indexhub_api && selectedReport.report_id){
      getChartByChartId()
    }
  }, [selectedReport])

  if (selectedReport.report_id && chartData.chart_id) {
    const option = {
      title: {
        text: chartData.title
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: Object.values(chartData.readable_names)
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      toolbox: {
        feature: {
          saveAsImage: {}
        }
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: chartData.chart_data.time
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: chartData.readable_names.rpt_actual,
          type: chartData.chart_type,
          stack: chartData.readable_names.rpt_actual,
          data: chartData.chart_data.rpt_actual
        },
        {
          name: chartData.readable_names.rpt_manual,
          type: chartData.chart_type,
          stack: chartData.readable_names.rpt_manual,
          data: chartData.chart_data.rpt_manual
        },
        {
          name: chartData.readable_names.rpt_forecast,
          type: chartData.chart_type,
          stack: chartData.readable_names.rpt_forecast,
          data: chartData.chart_data.rpt_forecast
        },
      ]
    };
    return (
      <VStack padding="10px">
        <Button onClick={() => clearSelectedReport()} colorScheme="teal" size="sm">
            View all reports
        </Button>
        <div><ReactEcharts option={option} style={{
                  height: '35rem',
                  width: '80vw',
                }}/></div>
      </VStack>
    )
  } else {
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
                return (
                  <Tr onClick={() => setSelectedReport(item)} key={item.report_id}>
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
    )
  }
}
