import { Accordion, AccordionButton, AccordionIcon, AccordionItem, AccordionPanel, Box, Button, CircularProgress, CircularProgressLabel, FormControl, FormLabel, HStack, Heading, Input, Modal, ModalBody, ModalCloseButton, ModalContent, ModalHeader, ModalOverlay, Spinner, Stack, Tab, TabIndicator, TabList, TableContainer, Tabs, Text, Tooltip, VStack, useDisclosure, useToast } from "@chakra-ui/react"
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
import { faCaretDown, faCaretUp, faChevronLeft, faChevronRight } from "@fortawesome/free-solid-svg-icons";
import { faCircleInfo, faFileChartColumn, faFileExport, faMicrochipAi, faPenToSquare, faWrench } from "@fortawesome/pro-light-svg-icons";
import Toast from "../../../components/toast";
import AiAnalysisModal from "./_includes/ai_analysis_modal";


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

const SEGMENTATION_TABS = ["volatility", "total value", "historical growth rate", "predicted growth rate"]

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

  const [cutoff, setCutoff] = useState<any[]>([])

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
    setCutoff(AIRecommendationTable["results"][0]["tables"])
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
          {policy ? (

            <HStack width="100%">
              <Stack>

                {/* Policy Description */}
                <Text mb="1.5rem !important">{policy["fields"]["description"]}</Text>
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
                <HStack alignItems="center" mb="1rem">
                  <Heading size="md" fontWeight="bold">Predicted Impact</Heading>
                  <Tooltip borderRadius={10} maxW="unset !important" label={
                    <Stack py="0.5rem" direction="row" spacing="0" justifyContent="space-evenly" alignItems="center">
                      <Box borderRight="1px solid #efeff1" px={{ base: '4', md: '6' }} py="1">
                        <Stack height="100%">
                          <VStack alignItems="flex-start">
                            <Heading size="sm" color="muted">
                              {mainStats[0]["title"]}
                            </Heading>
                            <Text mt="2px !important" fontSize="3xs" fontWeight="bold" textTransform="uppercase">{mainStats[0]["subtitle"]}</Text>
                          </VStack>
                          <Stack spacing="4" mt="auto">
                            <Text fontSize="xl" fontWeight="bold">{mainStats[0]["values"]["sum"]} %</Text>
                          </Stack>
                        </Stack>
                      </Box>
                      <Stack>
                        <Box px={{ base: '4', md: '6' }} py="1">
                          <Stack>
                            <VStack alignItems="flex-start">
                              <Heading size="sm" color="muted">
                                Frequency
                              </Heading>
                              <Text mt="2px !important" fontSize="3xs" fontWeight="bold" textTransform="uppercase">{policy["fields"]["freq"]}</Text>
                            </VStack>
                          </Stack>
                        </Box>
                        <Box px={{ base: '4', md: '6' }} py="1">
                          <Stack>
                            <VStack alignItems="flex-start">
                              <Heading size="sm" color="muted">
                                Forecast Horizon
                              </Heading>
                              <Text mt="2px !important" fontSize="3xs" fontWeight="bold" textTransform="uppercase">{policy["fields"]["fh"]}</Text>
                            </VStack>
                          </Stack>
                        </Box>
                      </Stack>
                    </Stack>
                  } placement='right'>
                    <FontAwesomeIcon icon={faCircleInfo as any} />
                  </Tooltip>
                </HStack>
                <hr></hr>
                <Stack mt="1.5rem" direction="row" spacing="0" justifyContent="space-evenly">
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack height="100%">
                      <VStack alignItems="flex-start">
                        <Heading size="sm" color="muted">
                          {mainStats[1]["title"]}
                        </Heading>
                        <Text mt="2px !important" fontSize="3xs" fontWeight="bold" textTransform="uppercase">{mainStats[1]["subtitle"]}</Text>
                      </VStack>
                      <Stack mt="auto !important">
                        <Text fontSize="3xl" fontWeight="bold" color={mainStats[1]["values"]["pct_change"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>{mainStats[1]["values"]["sum"]} </Text>
                        <HStack mt="unset !important" color={mainStats[1]["values"]["pct_change"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>
                          <Text fontSize="xs">(</Text>
                          <FontAwesomeIcon
                            style={{ marginRight: "3px", marginLeft: "unset" }}
                            icon={mainStats[1]["values"]["pct_change"] > 0 ? faCaretUp : faCaretDown}
                          />
                          <Text ml="unset !important" fontSize="xs" fontWeight="bold">
                            {Math.abs(mainStats[1]["values"]["pct_change"])}
                          </Text>
                          <Text fontSize="xs" ml="unset !important">)</Text>
                        </HStack>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack height="100%">
                      <VStack alignItems="flex-start">
                        <Heading size="sm" color="muted">
                          {mainStats[2]["title"]}
                        </Heading>
                        <Text mt="2px !important" fontSize="3xs" fontWeight="bold" textTransform="uppercase">{mainStats[2]["subtitle"]}</Text>
                      </VStack>
                      <Stack mt="auto !important">
                        <Text fontSize="3xl" fontWeight="bold" color={mainStats[2]["values"]["mean_pct"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>{mainStats[2]["values"]["sum"]}</Text>
                        <HStack mt="unset !important" color={mainStats[2]["values"]["mean_pct"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>
                          <Text fontSize="xs">(</Text>
                          <FontAwesomeIcon
                            style={{ marginRight: "3px", marginLeft: "unset" }}
                            icon={mainStats[2]["values"]["mean_pct"] > 0 ? faCaretUp : faCaretDown}
                          />
                          <Text ml="unset !important" fontSize="xs" fontWeight="bold">
                            {Math.abs(mainStats[2]["values"]["mean_pct"])}
                          </Text>
                          <Text fontSize="xs" ml="unset !important">)</Text>
                        </HStack>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack height="100%">
                      <VStack alignItems="flex-start">
                        <Heading size="sm" color="muted">
                          {mainStats[6]["title"]}
                        </Heading>
                        <Text mt="2px !important" fontSize="3xs" fontWeight="bold" textTransform="uppercase">{mainStats[6]["subtitle"]}</Text>
                      </VStack>
                      <Stack mt="auto !important">
                        <Text fontSize="3xl" fontWeight="bold">{mainStats[6]["values"]["progress"]} %</Text>
                        <Text mt="unset !important" fontSize="xs" fontWeight="bold">GOAL: {mainStats[5]["values"]["goal"]}%</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py="1" width="25%">
                    <Stack height="100%">
                      <VStack alignItems="flex-start">
                        <Heading size="sm" color="muted">
                          {mainStats[4]["title"]}
                        </Heading>
                        <Text mt="2px !important" fontSize="3xs" fontWeight="bold" textTransform="uppercase">{mainStats[4]["subtitle"]}</Text>
                      </VStack>
                      <Stack mt="auto !important">
                        <Text fontSize="3xl" fontWeight="bold">{mainStats[4]["values"]["n_improvement"]} / {mainStats[4]["values"]["n_entities"]}</Text>
                        <Text mt="unset !important" fontSize="xs" fontWeight="bold">{mainStats[7]["values"]["n_achievement"]} HAVE REACHED GOAL</Text>
                      </Stack>
                    </Stack>
                  </Box>
                </Stack>
              </Box>
            </Stack>

          ) : (
            <Stack width="100%" alignItems="center" justifyContent="center" height="full">
              <Spinner />
              <Text>Loading...</Text>
            </Stack>
          )}

          {/* Trend Chart */}
          <Box my="1.5rem !important" width="100%" height="27rem" p="1rem" backgroundColor="white" borderRadius="1rem">
            {mainTrendChart ? (
              <ReactEcharts
                option={mainTrendChart}
                style={{
                  height: "100%",
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
            <HStack justify="space-between">
              <Heading size="md" fontWeight="bold">AI Analyst Recommendations</Heading>
            </HStack>

            <Text mt="0.5rem !important" mb="1rem" fontSize="sm">The entities have been segmented based on their cumulative AI uplift and <b>{segmentationFactor}</b>. Entities highlighted in green represent recommended focus areas with low volatility and high uplift the implementation of AI. To view the statistics for each entity, click on the corresponding dot.</Text>
            <hr></hr>
            <Tabs mt="1.5rem" position="relative" variant="unstyled" isFitted isLazy lazyBehavior="keepMounted" onChange={(index: number) => setSegmentationFactor(SEGMENTATION_TABS[index])}>
              <TabList>
                <Tab fontWeight="bold">Volatility</Tab>
                <Tab fontWeight="bold">Total Value</Tab>
                <Tab fontWeight="bold">Historical Growth Rate</Tab>
                <Tab fontWeight="bold">Predicted Growth Rate</Tab>
              </TabList>
              <TabIndicator
                mt="-1.5px"
                height="2px"
                bg="blue.500"
                borderRadius="1px"
              />

            </Tabs>

            {/* Segmentation Plot */}
            <Box my="1.5rem !important" width="100%" height="27rem" p="1rem" backgroundColor="white" borderRadius="1rem">
              {segmentationPlot ? (
                <ReactEcharts
                  option={segmentationPlot}
                  style={{
                    height: "100%",
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

            <VStack width="100%" justify="space-between" mb="1rem" mt="2.5rem" alignItems="flex-start">

              <Heading size="md" fontWeight="bold">Forecast Selection</Heading>

              <HStack width="100%" justify="space-between">
                <Text fontSize="sm" width="70%">The entities in this table are sorted from highest uplift to lowest and the policy tracker represents the uplift % for each entity.</Text>
                <HStack>
                  <Button size="sm" onClick={() => {
                    getAIRecommendationTableApi(true)
                  }}>Show all entities</Button>
                  <Select
                    // onChange={(value) => {
                    //   if (value) {
                    //     setSegmentationFactor(value.value)
                    //   }
                    // }}
                    size="sm"
                    defaultValue={{
                      value: "increasing",
                      label: "High to Low"
                    }}
                    useBasicStyles
                    options={
                      [
                        {
                          "value": "increasing",
                          "label": "High to Low"
                        },
                        {
                          "value": "decreasing",
                          "label": "Low to High"
                        },
                      ]
                    }
                  />
                </HStack>
              </HStack>

              <Tooltip label="Execute Plan" placement='left'>
                <Button borderRadius="50px" width="60px" height="60px" position="fixed" bottom="50px" right="40px" zIndex="999" backgroundColor="black" onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "#676767" }} onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "black" }} isLoading={isExportingTable} onClick={() => {
                  exportRecommendationTable()
                }}>
                  <HStack>
                    <FontAwesomeIcon size="lg" color="white" icon={faFileExport as any} />
                  </HStack>
                </Button>
              </Tooltip>

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
                                <Button onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "#676767" }} onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "black" }} backgroundColor="black" onClick={(e) => {
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

                              <HStack width="80%" alignItems="stretch">

                                <Box
                                  px={{ base: '4', md: '6' }}
                                  py={{ base: '5', md: '6' }}
                                  bg="bg-surface"
                                  width={`${100 / 3}%`}
                                >
                                  <Stack>
                                    <Stack justify="space-between">
                                      <Text color="muted" fontWeight="bold">
                                        AI Forecast
                                      </Text>
                                      <Text color="muted" mt="unset !important" fontSize="3xs" textTransform="uppercase" fontWeight="bold">
                                        Over Next {policy["fields"]["fh"]} {FREQDISPLAYMAPPING[policy["fields"]["freq"]]}
                                      </Text>
                                    </Stack>
                                    <HStack justify="space-between">
                                      <Text fontSize="larger" fontWeight="bold">{entity_data["stats"]["current_window__stat"]}</Text>

                                      <HStack color={entity_data["stats"]["pct_change"] > 0 ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}>
                                        <Text>(</Text>
                                        <FontAwesomeIcon
                                          style={{ marginRight: "3px", marginLeft: "unset" }}
                                          icon={entity_data["stats"]["pct_change"] > 0 ? faCaretUp : faCaretDown}
                                        />
                                        <Text ml="unset !important" fontSize="xs" fontWeight="bold">
                                          {Math.abs(entity_data["stats"]["pct_change"])}
                                        </Text>
                                        <Text ml="unset !important">)</Text>
                                      </HStack>
                                    </HStack>
                                    <Text fontSize="xs">Predicted to {entity_data["stats"]["pct_change"] >= 0 ? "increase" : "decrease"} by <b>{Math.abs(entity_data["stats"]["diff"])}</b> from <b>{entity_data["stats"]["last_window__stat"]}</b> over the next {policy["fields"]["fh"]} {FREQDISPLAYMAPPING[policy["fields"]["freq"]]}</Text>
                                  </Stack>
                                </Box>
                                <Stack
                                  bg="bg-surface"
                                  width={`${100 / 3}%`}
                                  direction="column"
                                  justifyContent="space-between"
                                >
                                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
                                    <Stack>
                                      <HStack justify="space-between" alignItems="flex-start">
                                        <Stack>
                                          <Text color="muted" fontWeight="bold">
                                            Policy Tracker
                                          </Text>
                                          <Text color="muted" fontWeight="bold" mt="unset !important" fontSize="3xs" textTransform="uppercase">
                                            % UPLIFT FOR THE ENTITY
                                          </Text>
                                        </Stack>
                                        <CircularProgress capIsRound size="3rem" value={entity_data["stats"]["progress"] > 0 ? entity_data["stats"]["progress"] : 0} color='indicator.main_green'>
                                          <CircularProgressLabel fontSize="xs">{Math.floor(entity_data["stats"]["progress"] > 0 ? entity_data["stats"]["progress"] : 0)}%</CircularProgressLabel>
                                        </CircularProgress>
                                      </HStack>
                                      <VStack align="baseline">
                                        <Text fontSize="xs">AI has made an <b>overall progress of {entity_data["stats"]["progress"]}%</b> towards its goal of {entity_data["stats"]["goal"]}%, with an <b>average uplift of {entity_data["stats"]["score__uplift_pct__rolling_mean"]}%</b> over the last {FREQ_TO_SP[policy["fields"]["freq"]]} months</Text>
                                      </VStack>
                                    </Stack>
                                  </Box>
                                </Stack>
                                <Stack width={`${100 / 3}%`} justify="center">
                                  <ReactEcharts
                                    option={JSON.parse(entity_data["sparklines"])}
                                    style={{
                                      height: "100%",
                                      width: "100%",
                                    }}
                                  />
                                </Stack>
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
                    colorScheme="blackAlpha"
                    isDisabled={currentPageAIRecommendationTable == 1}
                  >
                    <FontAwesomeIcon icon={faChevronLeft} />
                  </Button>
                  <Text>{currentPageAIRecommendationTable}/{AIRecommendationTable["pagination"]["end"]}</Text>
                  <Button
                    onClick={() => setCurrentPageAIRecommendationTable(currentPageAIRecommendationTable + 1)}
                    colorScheme="blackAlpha"
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

        <AiAnalysisModal
          cutoff={cutoff}
          policy={policy}
          isOpenTrendModal={isOpenTrendModal}
          onCloseTrendModal={onCloseTrendModal}
          chartFilter={chartFilter}
          entityTrendChart={entityTrendChart}
        />

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