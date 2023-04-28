import { Accordion, AccordionButton, AccordionIcon, AccordionItem, AccordionPanel, Badge, Box, Button, CircularProgress, CircularProgressLabel, ExpandedIndex, FormControl, FormLabel, Grid, HStack, Heading, IconButton, Input, Modal, ModalBody, ModalCloseButton, ModalContent, ModalHeader, ModalOverlay, Progress, Spinner, Stack, StackDivider, TableContainer, Text, Tooltip, VStack, useDisclosure, useToast } from "@chakra-ui/react"
import { Select } from "chakra-react-select"
import React, { useEffect, useState } from "react"
import { useAuth0AccessToken } from "../../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../../..";
import { getPolicy } from "../../../utilities/backend_calls/policy";
import { Policy } from "../policies_dashboard";
import { useParams } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import ReactEcharts from "echarts-for-react";
import { exportAIRecommendationTable, getAIRecommendationTable } from "../../../utilities/backend_calls/tables";
import { createColumnHelper } from "@tanstack/react-table";
import { DataTable } from "../../../components/table";
import { getForecastPolicyStats } from "../../../utilities/backend_calls/stats";
import { colors } from "../../../theme/theme";
import { getSegmentationChart, getTrendChart } from "../../../utilities/backend_calls/charts";
import { faArrowTrendDown, faArrowTrendUp, faChevronLeft, faChevronRight } from "@fortawesome/free-solid-svg-icons";
import { capitalizeFirstLetter } from "../../../utilities/helpers";
import { faFileChartColumn, faFileExport, faMicrochipAi, faPenToSquare, faWrench } from "@fortawesome/pro-light-svg-icons";
import Toast from "../../../components/toast";


const FREQDISPLAYMAPPING: Record<string, string> = {
  "Hourly": "hourly",
  "Daily": "days",
  "Weekly": "weeks",
  "Monthly": "months",
  "Quarterly": "quarters",
  "Yearly": "years"
}

const FREQ_TO_SP: Record<string, number> = {
  "Hourly": 24,
  "Daily": 30,
  "Weekly": 52,
  "Monthly": 12,
}

type AIRecommendationTable = Record<string, any>
type mainStats = Record<string, any>[]

const PolicyForecast = () => {
  const { policy_id } = useParams()
  const [policy, setPolicy] = useState<Policy | null>(null)

  const [mainStats, setMainStats] = useState<mainStats | null>(null)

  const [chartFilter, setChartFilter] = useState<Record<string, string[]>>({})
  const [mainTrendChart, setMainTrendChart] = useState<Record<any, any> | null>(null)
  const [entityTrendChart, setEntityTrendChart] = useState<Record<any, any> | null>(null)
  const [segmentationPlot, setSegmentationPlot] = useState<Record<any, any> | null>(null)
  const [segmentationFactor, setSegmentationFactor] = useState("volatility")

  const [AIRecommendationTableFilter, setAIRecommendationTableFilter] = useState<Record<string, string[]>>({})
  const [AIRecommendationTable, setAIRecommendationTable] = useState<AIRecommendationTable | null>(null)
  const [AIRecommendationTableCache, setAIRecommendationTableCache] = useState<Record<number, AIRecommendationTable>>({})
  const [currentPageAIRecommendationTable, setCurrentPageAIRecommendationTable] = useState<number>(1)
  const [expandedEntityIndex, setExpandedEntityIndex] = useState<number>(0)
  const [manualOverrideEntity, setManualOverrideEntity] = useState<string>("")
  const [manualOverrideVal, setManualOverrideVal] = useState<string>("")
  const [executePlanCustomEntries, setExecutePlanCustomEntries] = useState<Record<string, any>[] | null>(null)
  const [isExportingTable, setIsExportingTable] = useState(false)


  const access_token_indexhub_api = useAuth0AccessToken();
  const user_details = useSelector((state: AppState) => state.reducer?.user);
  const toast = useToast();

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

  const insertExcecutePlanCustomEntries = (fh: number, ai: number, benchmark: number, override: number, use: string) => {
    if (AIRecommendationTable) {
      let internalExecutePlanCustomEntries = executePlanCustomEntries
      if (!internalExecutePlanCustomEntries) {
        internalExecutePlanCustomEntries = []
      }
      const existing_record_index = internalExecutePlanCustomEntries.findIndex(((obj: any) => (obj["fh"] == fh && obj["entity"] == AIRecommendationTable["results"][expandedEntityIndex]["entity"])))
      if (existing_record_index > -1) {
        internalExecutePlanCustomEntries.splice(existing_record_index, 1)
      }
      internalExecutePlanCustomEntries.push(
        {
          entity: AIRecommendationTable["results"][expandedEntityIndex]["entity"],
          fh: fh,
          ai: ai,
          benchmark: benchmark,
          override: override,
          use: use
        }
      )
      setExecutePlanCustomEntries(structuredClone(internalExecutePlanCustomEntries))

      AIRecommendationTable["results"][expandedEntityIndex]["tables"][fh - 1]["use_ai"] = false
      AIRecommendationTable["results"][expandedEntityIndex]["tables"][fh - 1]["use_benchmark"] = false
      AIRecommendationTable["results"][expandedEntityIndex]["tables"][fh - 1]["use_override"] = false

      AIRecommendationTable["results"][expandedEntityIndex]["tables"][fh - 1][`use_${use}`] = true
      setAIRecommendationTable(structuredClone(AIRecommendationTable))
    }
  }

  const manualOverrideAi = (manual_forecast = "", time_col: string) => {
    if (AIRecommendationTable) {
      if (expandedEntityIndex >= 0) {
        const upd_obj_index = AIRecommendationTable["results"][expandedEntityIndex]["tables"].findIndex(((obj: any) => obj["Time"] == time_col));
        AIRecommendationTable["results"][expandedEntityIndex]["tables"][upd_obj_index]["Override"] = Number(manual_forecast)
        setAIRecommendationTable(structuredClone(AIRecommendationTable))

        setManualOverrideEntity("")
        setManualOverrideVal("")
        onCloseManualOverrideModal()
      }
    }
  }

  const getEntityTrendChartApi = async () => {
    if (policy_id) {
      const entityTrendChart = await getTrendChart(
        policy_id,
        "single_forecast",
        access_token_indexhub_api,
        chartFilter
      );
      setEntityTrendChart(entityTrendChart);
    }
  };

  const exportRecommendationTable = async () => {
    if (policy_id && access_token_indexhub_api) {
      setIsExportingTable(true)
      const export_table_response = await exportAIRecommendationTable(
        policy_id,
        executePlanCustomEntries,
        access_token_indexhub_api
      );

      if (Object.keys(export_table_response).includes("path")) {
        Toast(
          toast,
          "Export Completed",
          `Path to your AI Recommendation file: ${export_table_response["path"]}`,
          "success"
        );
      } else {
        Toast(toast, "Export Failed", export_table_response["detail"], "error");
      }
      setIsExportingTable(false)
    }
  }

  const AI_Recommendation_column_helper = createColumnHelper<Record<string, any>>();

  const columns = [
    AI_Recommendation_column_helper.accessor("Time", {
      cell: (info) => (
        new Date(info.getValue()).toLocaleDateString()
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
        row["Time"],
        row["Override"],
      ],
      {
        id: "override",
        cell: (info) => {
          return (
            <HStack width="100%" justify="center">
              <Text width="60%" overflowX="scroll" color="table.font" fontSize="sm">{info.getValue()[1]}</Text>
              <Tooltip label="Edit Override Value">
                <Box width="40%" cursor="pointer">
                  <FontAwesomeIcon icon={faPenToSquare as any} size="lg" onClick={() => {
                    setManualOverrideEntity(info.getValue()[0])
                    onOpenManualOverrideModal()
                  }} />
                </Box>
              </Tooltip>
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

    AI_Recommendation_column_helper.accessor(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (row: any) => [
        row["Forecast Period"],
        row["Forecast"],
        row["Baseline"],
        row["Override"],
        row["use_ai"],
        row["use_benchmark"],
        row["use_override"]
      ],
      {
        id: "execute_plan",
        cell: (info) => {
          return (
            <HStack width="100%" justify="center">
              <Tooltip label="Use AI" >
                <Stack width={7} p={1} borderRadius={8} cursor="pointer" backgroundColor={info.getValue()[4] ? "table.icon_highlight" : ""}>
                  <FontAwesomeIcon icon={faMicrochipAi as any} size="lg" onClick={() => {
                    insertExcecutePlanCustomEntries(info.getValue()[0], info.getValue()[1], info.getValue()[2], info.getValue()[3], "ai")
                  }} />
                </Stack>
              </Tooltip>

              <Tooltip label="Use Benchmark">
                <Stack width={7} p={1} borderRadius={8} cursor="pointer" backgroundColor={info.getValue()[5] ? "table.icon_highlight" : ""}>
                  <FontAwesomeIcon icon={faFileChartColumn as any} size="lg" onClick={() => {
                    insertExcecutePlanCustomEntries(info.getValue()[0], info.getValue()[1], info.getValue()[2], info.getValue()[3], "benchmark")
                  }} />
                </Stack>
              </Tooltip>

              <Tooltip label={`Use Override ${info.getValue()[3] ? "" : "(Not Available)"}`}>
                <Stack width={7} p={1} borderRadius={8} cursor="pointer" backgroundColor={info.getValue()[6] ? "table.icon_highlight" : ""}>
                  <FontAwesomeIcon icon={faWrench as any} size="lg" onClick={() => {
                    if (info.getValue()[3]) {
                      insertExcecutePlanCustomEntries(info.getValue()[0], info.getValue()[1], info.getValue()[2], info.getValue()[3], "override")
                    }
                    // Consider adding some sort of notification to indicate 
                  }} />
                </Stack>
              </Tooltip>

            </HStack>
          );
        },
        header: "",
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
      policy["policy"]["outputs"] = JSON.parse(policy["policy"]["outputs"])
      policy["policy"]["sources"] = JSON.parse(policy["policy"]["sources"])
      setPolicy(policy["policy"]);
    };

    const getMainTrendChartApi = async () => {
      if (policy_id) {
        const mainTrendChart = await getTrendChart(
          policy_id,
          "single_forecast",
          access_token_indexhub_api
        );
        setMainTrendChart(mainTrendChart);
      }
    };

    const getForecastPolicyStatsApi = async () => {
      if (policy_id) {
        const forecastPolicyStats = await getForecastPolicyStats(policy_id, access_token_indexhub_api)
        setMainStats(forecastPolicyStats)
      }
    }

    if (access_token_indexhub_api && user_details.id && policy_id) {
      getPolicyApi()
      getMainTrendChartApi()
      getForecastPolicyStatsApi()
    }
  }, [access_token_indexhub_api, user_details, policy_id]);

  const getAIRecommendationTableApi = async (clear_filter = false) => {
    const filter_by = clear_filter ? {} : AIRecommendationTableFilter
    setAIRecommendationTable(null)
    const AIRecommendationTable = await getAIRecommendationTable(currentPageAIRecommendationTable, 5, policy_id ? policy_id : "", access_token_indexhub_api, filter_by)
    setAIRecommendationTable(AIRecommendationTable)
    AIRecommendationTableCache[currentPageAIRecommendationTable] = AIRecommendationTable
    setAIRecommendationTableCache(AIRecommendationTableCache)
  }

  useEffect(() => {

    if (access_token_indexhub_api && policy_id && currentPageAIRecommendationTable) {
      if (Object.keys(AIRecommendationTableCache).includes(currentPageAIRecommendationTable.toString())) {
        setAIRecommendationTable(AIRecommendationTableCache[currentPageAIRecommendationTable])
      } else {
        getAIRecommendationTableApi()
      }
    }
  }, [currentPageAIRecommendationTable, access_token_indexhub_api, policy_id])

  useEffect(() => {
    const getSegmentationPlot = async () => {
      if (policy_id) {
        setSegmentationPlot(null)
        const segmentationPlot = await getSegmentationChart(
          policy_id,
          "segment",
          access_token_indexhub_api,
          segmentationFactor
        );
        setSegmentationPlot(segmentationPlot);
      }
    };
    if (access_token_indexhub_api && policy_id && segmentationFactor) {
      getSegmentationPlot()
    }
  }, [segmentationFactor, access_token_indexhub_api, policy_id])

  if (policy) {
    return (
      <>
        <VStack width="100%" alignItems="flex-start">

          <Heading>AI Forecast</Heading>


          {/* Stats */}
          {mainStats ? (

            <HStack width="100%">
              <Stack>

                {/* Policy Description */}
                <Text mb="1.5rem !important">{policy["fields"]["description"]}</Text>
              </Stack>
              <Stack width="70%">
                <Box my="1.5rem !important" width="100%">
                  <Stack direction="row" divider={<StackDivider />} spacing="0" justifyContent="space-evenly">
                    <Box px="2" py={{ base: '5', md: '6' }} width="25%">
                      <Stack>
                        <VStack alignItems="flex-start">
                          <Heading size="sm" color="muted">
                            Level Columns
                          </Heading>
                        </VStack>
                        <Stack spacing="4">
                          <Text fontSize="2xl" fontWeight="bold">{policy["fields"]["level_cols"].join(", ")}</Text>
                        </Stack>
                      </Stack>
                    </Box>
                    <Box px="2" py={{ base: '5', md: '6' }} width="25%">
                      <Stack>
                        <VStack alignItems="flex-start">
                          <Heading size="sm" color="muted">
                            Frequency
                          </Heading>
                        </VStack>
                        <Stack spacing="4">
                          <Text fontSize="2xl" fontWeight="bold" >{capitalizeFirstLetter(policy["fields"]["freq"])}</Text>
                        </Stack>
                      </Stack>
                    </Box>
                    <Box px="2" py={{ base: '5', md: '6' }} width="25%">
                      <Stack>
                        <VStack alignItems="flex-start">
                          <Heading size="sm" color="muted">
                            Forecast Horizon
                          </Heading>
                        </VStack>
                        <Stack spacing="4">
                          <Text fontSize="2xl" fontWeight="bold" >{policy["fields"]["fh"]}</Text>
                        </Stack>
                      </Stack>
                    </Box>
                  </Stack>
                </Box>
              </Stack>
            </HStack>

          ) : (
            <Stack alignItems="center" justifyContent="center" height="full">
              <Spinner />
              <Text>Loading...</Text>
            </Stack>
          )}

          {mainStats ? (
            <Stack width="100%">
              <Box my="0.5rem !important" width="100%">
                <Stack direction="row" divider={<StackDivider />} spacing="0" justifyContent="space-evenly">

                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          {mainStats[0]["title"]}
                        </Heading>
                        <Text mt="unset !important" fontSize="smaller">{mainStats[0]["subtitle"]}</Text>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold">{mainStats[0]["values"]["sum"]}</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          {mainStats[5]["title"]}
                        </Heading>
                        <Text mt="unset !important" fontSize="smaller">{mainStats[5]["subtitle"]}</Text>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold">{mainStats[5]["values"]["goal"]} %</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          {mainStats[6]["title"]}
                        </Heading>
                        <Text mt="unset !important" fontSize="smaller">{mainStats[6]["subtitle"]}</Text>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold">{mainStats[6]["values"]["progress"]} %</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          {mainStats[7]["title"]}
                        </Heading>
                        <Text mt="unset !important" fontSize="smaller">{mainStats[7]["subtitle"]}</Text>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold">{mainStats[7]["values"]["n_achievement"]} out of {mainStats[7]["values"]["n_entities"]}</Text>
                      </Stack>
                    </Stack>
                  </Box>
                </Stack>
              </Box>
              <Box my="0.5rem !important" width="100%">
                <Stack direction="row" divider={<StackDivider />} spacing="0" justifyContent="space-evenly">
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          {mainStats[1]["title"]}
                        </Heading>
                        <Text mt="unset !important" fontSize="smaller">{mainStats[1]["subtitle"]}</Text>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold" color={mainStats[1]["values"]["pct_change"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>{mainStats[1]["values"]["sum"]} ({mainStats[1]["values"]["pct_change"]} %)</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          {mainStats[2]["title"]}
                        </Heading>
                        <Text mt="unset !important" fontSize="smaller">{mainStats[2]["subtitle"]}</Text>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold" color={mainStats[2]["values"]["mean_pct"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>{mainStats[2]["values"]["sum"]} ({mainStats[2]["values"]["mean_pct"]} %)</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          {mainStats[3]["title"]}
                        </Heading>
                        <Text mt="unset !important" fontSize="smaller">{mainStats[3]["subtitle"]}</Text>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold" color={mainStats[3]["values"]["rolling_mean_pct"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>{mainStats[3]["values"]["rolling_mean_pct"]} %</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          {mainStats[4]["title"]}
                        </Heading>
                        <Text mt="unset !important" fontSize="smaller">{mainStats[4]["subtitle"]}</Text>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold">{mainStats[4]["values"]["n_improvement"]} out of {mainStats[4]["values"]["n_entities"]}</Text>
                      </Stack>
                    </Stack>
                  </Box>
                </Stack>
              </Box>
            </Stack>

          ) : (
            <Stack alignItems="center" justifyContent="center" height="full">
              <Spinner />
              <Text>Loading...</Text>
            </Stack>
          )}

          {/* Trend Chart */}
          <Box my="1.5rem !important" width="100%" height="27rem">
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

          <Box my="1.5rem !important" width="100%" height="40rem">
            <HStack mb="1rem" justify="space-between" pr="1rem">
              <Heading fontWeight="bold">Top AI Recommendations</Heading>
            </HStack>

            <Text my="1.5rem !important">The entities have been segmented based on their cumulative AI uplift and <b>{segmentationFactor}</b>. For entities highlighted in green, it is recommended to override the benchmark with the AI forecast. To view the statistics for each entity, click on the corresponding dot.</Text>

            <FormControl width="20%">
              <FormLabel>
                Segmentation Factor
              </FormLabel>
              <Select
                onChange={(value) => {
                  if (value) {
                    setSegmentationFactor(value.value)
                  }
                }}
                defaultValue={{
                  value: "volatility",
                  label: "Volatility"
                }}
                useBasicStyles
                options={
                  [
                    {
                      "value": "volatility",
                      "label": "Volatility"
                    },
                    {
                      "value": "total value",
                      "label": "Total Value"
                    },
                    {
                      "value": "historical growth rate",
                      "label": "Historical Growth Rate"
                    },
                    {
                      "value": "predicted growth rate",
                      "label": "Predicted Growth Rate"
                    }
                  ]
                }
              />
            </FormControl>

            {/* Segmentation Plot */}
            <Box my="1.5rem !important" width="100%" height="27rem">
              {segmentationPlot ? (
                <ReactEcharts
                  option={segmentationPlot}
                  style={{
                    height: "27rem",
                    width: "100%",
                  }}
                  onEvents={{
                    "click": (param: any) => {
                      AIRecommendationTableFilter["entity"] = [param["seriesName"]]
                      setAIRecommendationTableFilter(AIRecommendationTableFilter)
                      getAIRecommendationTableApi()
                    }
                  }}
                />
              ) : (
                <Stack alignItems="center" justifyContent="center" height="full">
                  <Spinner />
                  <Text>Loading...</Text>
                </Stack>
              )}
            </Box>

            <VStack width="100%" justify="space-between" pr="1rem" mb="1rem" mt="2.5rem" alignItems="flex-start">
              <HStack width="100%" justify="center">
                <Button isLoading={isExportingTable} loadingText="Exporting table..." onClick={() => {
                  exportRecommendationTable()
                }}>
                  <HStack>
                    <Text>
                      Export Table
                    </Text>
                    <FontAwesomeIcon icon={faFileExport as any} />
                  </HStack>
                </Button>
              </HStack>

              <HStack width="100%" justify="space-between">
                <Text>The entities in this table are sorted from highest uplift to lowest and the policy tracker represents the uplift % for each entity.</Text>
                <Button onClick={() => {
                  getAIRecommendationTableApi(true)
                }}>Show all entities</Button>
              </HStack>
            </VStack>


            {AIRecommendationTable ? (
              <Box>
                <Accordion allowToggle onChange={(expanded_index: number) => { setExpandedEntityIndex(expanded_index) }}>
                  {AIRecommendationTable["results"].map((entity_data: any, idx: number) => {
                    return (
                      <AccordionItem key={idx}>
                        <h2>
                          <AccordionButton>
                            <HStack as="span" flex='1' textAlign='left'>
                              <VStack width="20%" alignItems="flex-start">
                                <Text pb="1rem" fontWeight="bold" fontSize="large">{entity_data["entity"]}</Text>
                                <Button backgroundImage="linear-gradient(to top right, #5353ff, #d81dd8)" onClick={(e) => {
                                  e.stopPropagation()
                                  chartFilter["entity"] = [entity_data["entity"]]
                                  setChartFilter(chartFilter)
                                  setEntityTrendChart(null)
                                  getEntityTrendChartApi()
                                  onOpenTrendModal()
                                }}>
                                  <HStack>
                                    <Text color="white">
                                      AI Analysis
                                    </Text>
                                    <FontAwesomeIcon color="white" icon={faMicrochipAi as any} />
                                  </HStack>

                                </Button>
                              </VStack>

                              <HStack width="80%">
                                <HStack width="70%" alignItems="stretch">
                                  <Box
                                    px={{ base: '4', md: '6' }}
                                    py={{ base: '5', md: '6' }}
                                    bg="bg-surface"
                                    borderRadius="lg"
                                    boxShadow="sm"
                                    width="50%"
                                  >
                                    <Stack>
                                      <HStack justify="space-between">
                                        <Text color="muted">
                                          AI Forecast (Next {policy["fields"]["fh"]} {FREQDISPLAYMAPPING[policy["fields"]["freq"]]})
                                        </Text>
                                      </HStack>
                                      <HStack justify="space-between">
                                        <Text fontSize="larger" fontWeight="bold">{entity_data["stats"]["current_window__sum"]}</Text>
                                        <Badge variant="subtle" colorScheme={entity_data["stats"]["pct_change"] > 0 ? "green" : "red"}>
                                          <HStack spacing="1">
                                            <FontAwesomeIcon
                                              color={entity_data["stats"]["pct_change"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}
                                              icon={entity_data["stats"]["pct_change"] > 0 ? faArrowTrendUp : faArrowTrendDown}
                                            />
                                            <Text>{entity_data["stats"]["pct_change"]}</Text>
                                          </HStack>
                                        </Badge>
                                      </HStack>
                                      <Text fontSize="sm">Predicted to {entity_data["stats"]["pct_change"] > 0 ? "increase" : "decrease"} by <b>{Math.abs(entity_data["stats"]["diff"])}</b> from <b>{entity_data["stats"]["last_window__sum"]}</b> over the next {policy["fields"]["fh"]} {FREQDISPLAYMAPPING[policy["fields"]["freq"]]}</Text>
                                    </Stack>
                                  </Box>
                                  <Stack
                                    bg="bg-surface"
                                    borderRadius="lg"
                                    boxShadow="sm"
                                    width="50%"
                                    direction="column"
                                    justifyContent="space-between"
                                  >
                                    <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
                                      <Stack>
                                        <HStack justify="space-between" alignItems="flex-start">
                                          <Text color="muted">
                                            Policy Tracker
                                          </Text>
                                          <CircularProgress capIsRound size="3rem" value={entity_data["stats"]["progress"] > 0 ? entity_data["stats"]["progress"] : 0} color='indicator.main_green'>
                                            <CircularProgressLabel fontSize="xs">{Math.floor(entity_data["stats"]["progress"] > 0 ? entity_data["stats"]["progress"] : 0)}%</CircularProgressLabel>
                                          </CircularProgress>
                                        </HStack>
                                        <VStack align="baseline">
                                          {/* <Text fontSize="larger" fontWeight="bold">{entity_data["stats"]["score__uplift_pct__rolling_mean"] > 0 ? entity_data["stats"]["score__uplift_pct__rolling_mean"] : 0} %</Text> */}
                                          {/* <CircularProgress capIsRound size="3rem" value={entity_data["stats"]["score__uplift_pct__rolling_mean"] > 0 ? entity_data["stats"]["score__uplift_pct__rolling_mean"] : 0} color='indicator.main_green'>
                                            <CircularProgressLabel fontSize="small">{entity_data["stats"]["score__uplift_pct__rolling_mean"] > 0 ? entity_data["stats"]["score__uplift_pct__rolling_mean"] : 0}%</CircularProgressLabel>
                                          </CircularProgress> */}
                                          <Text fontSize="sm">AI has made an <b>overall progress of {entity_data["stats"]["progress"]}%</b> towards its goal of {entity_data["stats"]["goal"]}%, with an <b>average uplift of {entity_data["stats"]["score__uplift_pct__rolling_mean"]}%</b> over the last {FREQ_TO_SP[policy["fields"]["freq"]]} months</Text>
                                        </VStack>
                                      </Stack>
                                    </Box>
                                    {/* <Progress value={entity_data["stats"]["score__uplift_pct__rolling_mean"] > 0 ? entity_data["stats"]["score__uplift_pct__rolling_mean"] : 0} size="xs" borderRadius="none" bg="bg-surface" /> */}
                                  </Stack>
                                </HStack>
                                <HStack width="30%" justify="center">

                                </HStack>
                              </HStack>
                            </HStack>
                            <AccordionIcon />
                          </AccordionButton>
                        </h2>
                        <AccordionPanel pb={4}>
                          <TableContainer width="100%" backgroundColor="white" borderRadius={8}>
                            <DataTable
                              columns={columns}
                              data={entity_data["tables"]}
                              body_height="73px"
                            ></DataTable>
                          </TableContainer>
                        </AccordionPanel>
                      </AccordionItem>
                    )
                  })}
                </Accordion>

                <HStack py="1rem" width="100%" justify="right">
                  <Button
                    onClick={() => setCurrentPageAIRecommendationTable(currentPageAIRecommendationTable - 1)}
                    colorScheme="facebook"
                    isDisabled={currentPageAIRecommendationTable == 1}
                  >
                    <FontAwesomeIcon icon={faChevronLeft} />
                  </Button>
                  <Text>{currentPageAIRecommendationTable}/{AIRecommendationTable["pagination"]["end"]}</Text>
                  <Button
                    onClick={() => setCurrentPageAIRecommendationTable(currentPageAIRecommendationTable + 1)}
                    colorScheme="facebook"
                    isDisabled={currentPageAIRecommendationTable == AIRecommendationTable["pagination"]["end"]}
                  >
                    <FontAwesomeIcon icon={faChevronRight} />
                  </Button>
                </HStack>
              </Box>
            ) : (
              <Stack alignItems="center" justifyContent="center" height="full">
                <Spinner />
                <Text>Loading...</Text>
              </Stack>
            )}
          </Box>

        </VStack>

        {/* Modal for trends */}
        <Modal isOpen={isOpenTrendModal} onClose={onCloseTrendModal} size="6xl">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <Stack>
                <HStack>
                  {Object.keys(chartFilter).map((filter_key, idx) => {
                    return (
                      <Box
                        key={idx}
                        px={{ base: '4', md: '6' }}
                        py={{ base: '5', md: '6' }}
                        bg="lists.bg_grey"
                        borderRadius="lg"
                        boxShadow="lg"
                        minWidth="15rem"
                      >
                        <Stack>
                          <Text fontSize="sm" color="muted">
                            {filter_key}
                          </Text>
                          <Heading size={{ base: 'sm', md: 'md' }}>{chartFilter[filter_key]}</Heading>
                        </Stack>
                      </Box>
                    )
                  })}
                </HStack>
                <Box my="1.5rem !important" width="100%" height="27rem">
                  {entityTrendChart ? (
                    <ReactEcharts
                      option={entityTrendChart}
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
              </Stack>
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
                  {(AIRecommendationTable && expandedEntityIndex > -1) && (
                    <FormLabel>
                      {AIRecommendationTable["results"][expandedEntityIndex]["entity"]} ({new Date(manualOverrideEntity).toLocaleDateString()})
                    </FormLabel>
                  )}
                  <Input
                    onChange={(e) => (setManualOverrideVal(e.currentTarget.value))}
                  />
                  <Stack py="1rem" width="100%" alignItems="center">
                    <Button width="50%" onClick={() => {
                      if (isNaN(+manualOverrideVal)) {
                        Toast(toast, "Invalid Value", "Use only numbers as override values", "error");
                      } else {
                        manualOverrideAi(manualOverrideVal, manualOverrideEntity)
                      }
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
  } else {
    return (
      <Stack alignItems="center" justifyContent="center" height="full">
        <Spinner />
        <Text>Loading...</Text>
      </Stack>
    )
  }
}

export default PolicyForecast