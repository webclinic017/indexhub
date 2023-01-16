import React, { useState } from "react";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0"
import { AppState } from "../../index";
import { useDispatch,useSelector } from "react-redux";
import { createReport, getReport, deleteReport} from "../../utilities/backend_calls/report";
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
  Box,
  Heading,
  Progress,
  Stack,
  Text,
  useColorModeValue,
  SimpleGrid,
  Badge
} from "@chakra-ui/react"
import Forecast_Recommendations from "./report_types/forecast_prediction";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faArrowsRotate,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";

export type Report = {
  report_id: string,
  source_id: string,
  source_name: string,
  entities: Record<string, any>,
  user_id: string,
  chart_id: string,
  table_id: string,
  status: string,
  created_at: string,
  completed_at: string,
  filters: Record<string, any>
}

const getStatusColor = (status: string) => {
  switch(status){
    case "COMPLETE": {
      return "green"
    }
    case "RUNNING": {
      return "yellow"
    }
    case "ERROR": {
      return "red"
    }
  }
}

export default function Reports() {
  const access_token_indexhub_api = useAuth0AccessToken()
  const dispatch = useDispatch()
  const [reports, setReports] = useState<{reports: Report[]}>({reports: []})
  const [current_pagination, setCurrentPagination] = useState(1)
  const [selectedReport, setSelectedReport] = useState<Report>({report_id: "", source_id: "", source_name: "", entities: {}, user_id: "", chart_id: "", table_id: "", status: "", created_at: "",completed_at: "",  filters: {}});

  const clearSelectedReport = () => {
    setSelectedReport({report_id: "", source_id: "", source_name: "", entities: {}, user_id: "", chart_id: "", table_id: "", status: "", created_at: "",completed_at: "",  filters: {}})
  }

  const stats = [
    { label: 'Complete', value: reports?.reports?.reduce((n, report) => n + (Number(report.status === "COMPLETE")), 0), limit: reports?.reports?.length , color:"green"},
    { label: 'Running', value: reports?.reports?.reduce((n, report) => n + (Number(report.status === "RUNNING")), 0), limit: reports?.reports?.length , color: "yellow"},
    { label: 'Failed', value: reports?.reports?.reduce((n, report) => n + (Number(report.status === "FAILED")), 0), limit: reports?.reports?.length, color:"red"},
  ]

  const report_ids = useSelector(
    (state: AppState) => state.reducer?.report_ids
  );
  const user_details = useSelector(
    (state: AppState) => state.reducer?.user
  );

  const reports_per_page = 5
  const start_index = (current_pagination - 1) * reports_per_page
  const pages_required = Math.ceil(reports.reports?.length/reports_per_page)

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
        <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">Reports</Text>
        {reports?.reports?.length > 0 ? (
          <>
            <VStack backgroundColor="white" width="100%" borderRadius="8px" box-shadow="0px 0px 1px rgba(48, 49, 51, 0.05),0px 2px 4px rgba(48, 49, 51, 0.1)">
              <Container margin="1rem 0 4rem" maxWidth="unset">
                <SimpleGrid columns={{ base: 1, md: 3 }} gap={{ base: '5', md: '6' }}>
                  {stats.map((stat, id) => {
                    return(
                      <Box key={id} bg="bg-surface" boxShadow={useColorModeValue('sm', 'sm-dark')}>
                        <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
                          <Stack>
                            <Text fontSize="sm">
                              {stat.label}
                            </Text>
                            <Stack direction="row" align="baseline">
                              <Heading>{stat.value}</Heading>
                              <Text aria-hidden fontWeight="semibold">
                                / {stat.limit}
                              </Text>
                              <Box srOnly>out of {stat.limit}</Box>
                            </Stack>
                          </Stack>
                        </Box>
                        <Progress value={(stat.value / stat.limit) * 100} size="xs" borderRadius="none" colorScheme={stat.color} bg="bg-surface"/>
                      </Box>
                    )
                    })}
                </SimpleGrid>
              </Container>
              <TableContainer width="100%" backgroundColor="white">
                <Table>
                  <Thead backgroundColor="table.header_background">
                    <Tr borderTop="1px solid" borderTopColor="table.border">
                      <Th fontSize="xs">Source</Th>
                      <Th fontSize="xs">Entities</Th>
                      <Th fontSize="xs">Created at</Th>
                      <Th fontSize="xs">Completed at</Th>
                      <Th fontSize="xs" width="200px" textAlign="center">Status</Th>
                      <Th fontSize="xs" width="100px"></Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {reports.reports.slice(start_index, start_index + reports_per_page).map((item) => {
                      const created_at_date = new Date(item.created_at).toLocaleString()
                      let completed_at_date = ""
                      if (item.completed_at) {
                        completed_at_date = new Date(item.completed_at).toLocaleString()
                      }
                      return (
                        <Tr height="73px" key={item.report_id}>
                          <Td fontSize="sm"  onClick={() => setSelectedReport(item)}><Text cursor="pointer">{item.source_name}</Text></Td>
                          <Td fontSize="sm" >{Object.keys(item.entities["forecast_recommendations"]).join(", ")}</Td>
                          <Td fontSize="sm" >{created_at_date}</Td>
                          <Td fontSize="sm" >{completed_at_date}</Td>
                          <Td textAlign="center">
                            <Badge borderRadius="35px" paddingInline="1rem" textTransform="lowercase" fontSize="sm" colorScheme={getStatusColor(item.status)}>
                              {item.status.toLowerCase()}
                            </Badge>
                          </Td>
                          <Td>
                            <HStack justifyContent="space-between">
                              <FontAwesomeIcon cursor="pointer" icon={faArrowsRotate} onClick={() => createReport(user_details.user_id, access_token_indexhub_api, dispatch, item.report_id)}/>
                              <FontAwesomeIcon cursor="pointer" icon={faTrash} onClick={async () => setReports(await deleteReport(access_token_indexhub_api, item.report_id))}/>
                            </HStack>
                          </Td>
                        </Tr>
                      )
                    })}
                  </Tbody>
                </Table>
              </TableContainer>
              <HStack padding="0 25px" marginTop="20px !important" marginBottom="20px !important" justifyContent="space-between" width="100%">
                <Text fontSize="sm" >Showing {current_pagination} of {pages_required} pages</Text>
                <HStack>
                  <Button onClick={() => setCurrentPagination(current_pagination - 1)} isDisabled={current_pagination == 1}>Previous</Button>
                  <Button onClick={() => setCurrentPagination(current_pagination + 1)} isDisabled={current_pagination == pages_required}>Next</Button>
                </HStack>
              </HStack>
            </VStack>
            <Button colorScheme="facebook" size="sm" onClick={() => createReport(user_details.user_id, access_token_indexhub_api, dispatch)}>
              Create Report
            </Button>
          </>
        ): (
          <Box width="100%" as="section" bg="bg-surface">
            <Container maxWidth="unset" py={{ base: '16', md: '24' }}>
              <Stack spacing={{ base: '8', md: '10' }}>
                <Stack spacing={{ base: '4', md: '5' }} align="center">
                  <Heading>Ready to Grow?</Heading>
                  <Text  color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                    With these comprehensive reports you will be able to analyse the past with statistical context and look into the future of what you care most!
                  </Text>
                </Stack>
                <Stack spacing="3" direction={{ base: 'column', sm: 'row' }} justify="center">
                  <Button colorScheme="facebook" size="lg" onClick={() => createReport(user_details.user_id, access_token_indexhub_api, dispatch)}>
                    Create Report
                  </Button>
                </Stack>
              </Stack>
            </Container>
          </Box>
        )}
      </VStack>
    )
  }
}
