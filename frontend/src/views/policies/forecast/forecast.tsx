import { Accordion, AccordionButton, AccordionIcon, AccordionItem, AccordionPanel, Box, Button, ExpandedIndex, FormControl, FormLabel, HStack, Heading, Input, Modal, ModalBody, ModalCloseButton, ModalContent, ModalHeader, ModalOverlay, Spinner, Stack, StackDivider, TableContainer, Text, VStack, useDisclosure } from "@chakra-ui/react"
import { Select } from "chakra-react-select"
import React, { useEffect, useState } from "react"
import { useAuth0AccessToken } from "../../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../../..";
import { getPolicy } from "../../../utilities/backend_calls/policy";
import { Policy } from "../policies_dashboard";
import { useParams } from "react-router-dom";
import { Stat } from "../../../components/stats";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPenToSquare } from "@fortawesome/free-regular-svg-icons";
import ReactEcharts from "echarts-for-react";
import { getAIRecommendationTable } from "../../../utilities/backend_calls/tables";
import { createColumnHelper } from "@tanstack/react-table";
import { DataTable } from "../../../components/table";
import { getForecastPolicyStats } from "../../../utilities/backend_calls/stats";
import { colors } from "../../../theme/theme";
import { getTrendChart } from "../../../utilities/backend_calls/charts";

const dummy_stats = [
  { label: 'Total Subscribers', value: '71,887', delta: { value: '321', isUpwardsTrend: true } },
  { label: 'Avg. Open Rate', value: '56.87%', delta: { value: '2.3%', isUpwardsTrend: true } },
  { label: 'Avg. Click Rate', value: '12.87%', delta: { value: '0.1%', isUpwardsTrend: false } },
]

type AIRecommendationTable = Record<string, any>[]
type mainStats = Record<string, any>[]

const PolicyForecast = () => {
  const { policy_id } = useParams()
  const [policy, setPolicy] = useState<Policy | null>(null)
  const [mainTrendChart, setMainTrendChart] = useState<Record<any, any> | null>(null)
  const [AIRecommendationTable, setAIRecommendationTable] = useState<AIRecommendationTable | null>(null)
  const [mainStats, setMainStats] = useState<mainStats | null>(null)

  const access_token_indexhub_api = useAuth0AccessToken();
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  const [expandedEntityIndex, setExpandedEntityIndex] = useState<number>(0)
  const [manualOverrideEntity, setManualOverrideEntity] = useState<string>("")
  const [manualOverrideVal, setManualOverrideVal] = useState<string>("")

  const {
    isOpen: isOpenTrendModal,
    onOpen: onOpenTrendModal,
    onClose: onCloseTrendModal
  } = useDisclosure()
  const {
    isOpen: isOpenManualOverrideModal,
    onOpen: onOpenManualOverrideModal,
    onClose: onCloseManualOverrideModal
  } = useDisclosure()

  const manualOverrideAi = (manual_forecast = "", time_col: string) => {
    if (AIRecommendationTable) {
      if (expandedEntityIndex >= 0) {
        const upd_obj_index = AIRecommendationTable[expandedEntityIndex]["table"].findIndex(((obj: any) => obj["time_col"] == time_col));
        AIRecommendationTable[expandedEntityIndex]["table"][upd_obj_index]["Override"] = manual_forecast
        setAIRecommendationTable(structuredClone(AIRecommendationTable))

        setManualOverrideEntity("")
        setManualOverrideVal("")
        onCloseManualOverrideModal()
      }
    }
  }

  const AI_Recommendation_column_helper = createColumnHelper<Record<string, any>>();

  const columns = [
    AI_Recommendation_column_helper.accessor("time_col", {
      cell: (info) => (
        info.getValue()
      ),
      header: "Time",
    }),

    AI_Recommendation_column_helper.accessor("Forecast Period", {
      cell: (info) => (
        info.getValue()
      ),
      header: "Forecast Period",
    }),

    AI_Recommendation_column_helper.accessor("Baseline", {
      cell: (info) => (
        info.getValue()
      ),
      header: "Baseline",
    }),

    AI_Recommendation_column_helper.accessor("Forecast", {
      cell: (info) => (
        info.getValue()
      ),
      header: "Forecast",
    }),

    AI_Recommendation_column_helper.accessor("Forecast (90% quantile)", {
      cell: (info) => (
        info.getValue()
      ),
      header: "Forecast (90% quantile)",
    }),

    AI_Recommendation_column_helper.accessor("Forecast (10% quantile)", {
      cell: (info) => (
        info.getValue()
      ),
      header: "Forecast (10% quantile)",
    }),

    AI_Recommendation_column_helper.accessor(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (row: any) => [
        row["time_col"],
        row["Override"],
      ],
      {
        id: "override",
        cell: (info) => {
          return (
            <HStack width="100%" justify="center">
              <Text width="60%" overflowX="scroll">{info.getValue()[1]}</Text>
              <Box width="40%">
                <FontAwesomeIcon icon={faPenToSquare} size="lg" onClick={() => {
                  setManualOverrideEntity(info.getValue()[0])
                  onOpenManualOverrideModal()
                }} />
              </Box>
            </HStack>
          );
        },
        header: "Override",
        meta: {
          isButtons: true,
        },
        enableSorting: false,
      }
    ),
  ];

  useEffect(() => {
    const getPolicyApi = async () => {
      const policy = await getPolicy(
        "",
        policy_id,
        access_token_indexhub_api
      );
      policy["policy"]["fields"] = JSON.parse(policy["policy"]["fields"])
      setPolicy(policy["policy"]);
    };

    const getMainTrendChartApi = async () => {
      const mainTrendChart = await getTrendChart(
        policy_id,
        "",
        access_token_indexhub_api
      );
      setMainTrendChart(mainTrendChart);
    };

    const getAIRecommendationTableApi = async () => {
      const AIRecommendationTable = await getAIRecommendationTable()
      setAIRecommendationTable(AIRecommendationTable)
    }

    const getForecastPolicyStatsApi = async () => {
      const forecastPolicyStats = await getForecastPolicyStats()
      setMainStats(forecastPolicyStats)
    }

    if (access_token_indexhub_api && user_details.id) {
      getPolicyApi();
      getMainTrendChartApi()
      getAIRecommendationTableApi()
      getForecastPolicyStatsApi()
    }
  }, [access_token_indexhub_api, user_details]);


  // useEffect(() => {
  //   console.log(policy)
  // }, [policy])

  // useEffect(() => {
  //   console.log(mainTrendChart)
  // }, [mainTrendChart])

  // useEffect(() => {
  //   console.log(AIRecommendationTable)
  // }, [AIRecommendationTable])

  // useEffect(() => {
  //   console.log(expandedEntityIndex)
  // }, [expandedEntityIndex])

  useEffect(() => {
    console.log(mainStats)
  }, [mainStats])


  // if (true) {
  return (
    <>
      <VStack width="100%" alignItems="flex-start">

        <Heading>AI Forecast</Heading>

        {/* Policy Description */}
        {/* <Text mb="1.5rem !important">{policy["fields"]["description"]}</Text> */}

        {/* Variables */}
        <HStack width="60%" my="1.5rem !important">
          <FormControl>
            <FormLabel>
              Level columns
            </FormLabel>
            <Select
              useBasicStyles
            />
          </FormControl>
          <FormControl>
            <FormLabel>
              Frequency
            </FormLabel>
            <Select
              useBasicStyles
            />
          </FormControl>
          <FormControl>
            <FormLabel>
              Forecast horizon
            </FormLabel>
            <Select
              useBasicStyles
            />
          </FormControl>
        </HStack>

        {/* Stats */}
        {mainStats ? (
          <Box my="1.5rem !important" width="100%">
            <Stack direction="row" divider={<StackDivider />} spacing="0" justifyContent="space-evenly">
              <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
                <Stack>
                  <VStack alignItems="flex-start">
                    <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                      {mainStats[0]["title"]}
                    </Heading>
                    <Text mt="unset" fontSize="smaller">{mainStats[0]["subtitle"]}</Text>
                  </VStack>
                  <Stack spacing="4">
                    <Text fontSize="2xl" fontWeight="bold">{mainStats[0]["values"]["sum"]}</Text>
                  </Stack>
                </Stack>
              </Box>
              <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
                <Stack>
                  <VStack alignItems="flex-start">
                    <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                      {mainStats[1]["title"]}
                    </Heading>
                    <Text mt="unset" fontSize="smaller">{mainStats[1]["subtitle"]}</Text>
                  </VStack>
                  <Stack spacing="4">
                    <Text fontSize="2xl" fontWeight="bold" color={mainStats[1]["values"]["pct_change"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>{mainStats[1]["values"]["sum"]} ({mainStats[1]["values"]["pct_change"]})</Text>
                  </Stack>
                </Stack>
              </Box>
              <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
                <Stack>
                  <VStack alignItems="flex-start">
                    <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                      {mainStats[2]["title"]}
                    </Heading>
                    <Text mt="unset" fontSize="smaller">{mainStats[2]["subtitle"]}</Text>
                  </VStack>
                  <Stack spacing="4">
                    <Text fontSize="2xl" fontWeight="bold" color={mainStats[2]["values"]["mean_pct"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>{mainStats[2]["values"]["sum"]} ({mainStats[2]["values"]["mean_pct"]})</Text>
                  </Stack>
                </Stack>
              </Box>
            </Stack>
          </Box>

        ) : (
          <Stack alignItems="center" justifyContent="center" height="full">
            <Spinner />
            <Text>Loading...</Text>
          </Stack>
        )}

        {/* Trend Chart */}
        <Box my="1.5rem !important" width="100%">
          {mainTrendChart ? (
            <ReactEcharts
              option={mainTrendChart}
              style={{
                height: "27rem",
                width: "100%",
              }}
            />
          ) : (
            <Stack alignItems="center" justifyContent="center" height="full">
              <Spinner />
              <Text>Loading...</Text>
            </Stack>
          )}

        </Box>



        {/* Top AI Recommendations */}
        {AIRecommendationTable ? (
          <Box my="1.5rem !important" width="100%">
            <HStack mb="1rem" justify="space-between" pr="1rem">
              <Text fontWeight="bold">Top AI Recommendations Table</Text>
              <Button>Export</Button>
            </HStack>
            <Accordion allowToggle onChange={(expanded_index: number) => { setExpandedEntityIndex(expanded_index) }}>
              {AIRecommendationTable.map((entity, idx) => {
                return (
                  <AccordionItem key={idx}>
                    <h2>
                      <AccordionButton>
                        <Box as="span" flex='1' textAlign='left'>
                          {entity["state"]}
                        </Box>
                        <AccordionIcon />
                      </AccordionButton>
                    </h2>
                    <AccordionPanel pb={4}>
                      <TableContainer width="100%" backgroundColor="white">
                        <DataTable
                          columns={columns}
                          data={entity["table"]}
                          body_height="73px"
                        ></DataTable>
                      </TableContainer>
                    </AccordionPanel>
                  </AccordionItem>
                )
              })}
            </Accordion>
          </Box>
        ) : (
          <Stack alignItems="center" justifyContent="center" height="full">
            <Spinner />
            <Text>Loading...</Text>
          </Stack>
        )}


        {/* Top Predicted Growth */}
        {/* <Box my="1.5rem !important" width="100%">
            <HStack mb="1rem" justify="space-between" pr="1rem">
              <Text fontWeight="bold">Top Predicted Growth Table</Text>
              <Button>Export</Button>
            </HStack>
            <TableContainer width="100%" backgroundColor="white">
              <DataTable
                columns={columns}
                data={AIRecommendationTable}
                body_height="73px"
              ></DataTable>
            </TableContainer>
          </Box> */}

        {/* Top Predicted Decline */}
        {/* <Box my="1.5rem !important" width="100%">
            <HStack mb="1rem" justify="space-between" pr="1rem">
              <Text fontWeight="bold">Top Predicted Decline Table</Text>
              <Button>Export</Button>
            </HStack>
            <TableContainer width="100%" backgroundColor="white">
              <DataTable
                columns={columns}
                data={AIRecommendationTable}
                body_height="73px"
              ></DataTable>
            </TableContainer>
          </Box> */}
      </VStack>

      {/* Modal for trends */}
      <Modal isOpen={isOpenTrendModal} onClose={onCloseTrendModal} size="6xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            <Text>Credentials</Text>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody py="15rem">
            Trend chart here
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Modal for manual overrides */}
      <Modal isOpen={isOpenManualOverrideModal} onClose={onCloseManualOverrideModal}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            <Text>Manual Override</Text>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Stack>
              <FormControl>
                <FormLabel>
                  {manualOverrideEntity}
                </FormLabel>
                <Input
                  onChange={(e) => (setManualOverrideVal(e.currentTarget.value))}
                />
                <Stack py="1rem" width="100%" alignItems="center">
                  <Button width="50%" onClick={() => {
                    manualOverrideAi(manualOverrideVal, manualOverrideEntity)
                  }}>
                    Override
                  </Button>
                </Stack>
              </FormControl>
            </Stack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  )
  // } else {
  //   return (
  //     <Stack alignItems="center" justifyContent="center" height="full">
  //       <Spinner />
  //       <Text>Loading...</Text>
  //     </Stack>
  //   )
  // }
}

export default PolicyForecast