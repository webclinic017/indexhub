import { Accordion, AccordionButton, AccordionIcon, AccordionItem, AccordionPanel, Badge, Box, Button, ExpandedIndex, FormControl, FormLabel, Grid, HStack, Heading, Input, Modal, ModalBody, ModalCloseButton, ModalContent, ModalHeader, ModalOverlay, Progress, Spinner, Stack, StackDivider, TableContainer, Text, VStack, useDisclosure } from "@chakra-ui/react"
import { Select } from "chakra-react-select"
import React, { useEffect, useState } from "react"
import { useAuth0AccessToken } from "../../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../../..";
import { getPolicy } from "../../../utilities/backend_calls/policy";
import { Policy } from "../policies_dashboard";
import { useParams } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPenToSquare } from "@fortawesome/free-regular-svg-icons";
import ReactEcharts from "echarts-for-react";
import { getAIRecommendationTable } from "../../../utilities/backend_calls/tables";
import { createColumnHelper } from "@tanstack/react-table";
import { DataTable } from "../../../components/table";
import { getForecastPolicyStats } from "../../../utilities/backend_calls/stats";
import { colors } from "../../../theme/theme";
import { getSegmentationChart, getTrendChart } from "../../../utilities/backend_calls/charts";
import { faArrowTrendDown, faArrowTrendUp, faChevronLeft, faChevronRight } from "@fortawesome/free-solid-svg-icons";
import { capitalizeFirstLetter } from "../../../utilities/helpers";


const FREQDISPLAYMAPPING: Record<string, string> = {
  "Daily": "days",
  "Weekly": "weeks",
  "Monthly": "months",
  "Quarterly": "quarters",
  "Yearly": "years"
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


  const access_token_indexhub_api = useAuth0AccessToken();
  const user_details = useSelector((state: AppState) => state.reducer?.user);

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
        const upd_obj_index = AIRecommendationTable["results"][expandedEntityIndex]["tables"].findIndex(((obj: any) => obj["Time"] == time_col));
        AIRecommendationTable["results"][expandedEntityIndex]["tables"][upd_obj_index]["Override"] = manual_forecast
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

          {/* Policy Description */}
          <Text mb="1.5rem !important">{policy["fields"]["description"]}</Text>

          {/* Stats */}
          {mainStats ? (
            <Stack width="100%">
              <Box my="1.5rem !important" width="100%">
                <Stack direction="row" divider={<StackDivider />} spacing="0" justifyContent="space-evenly">
                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          Level Columns
                        </Heading>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold">{policy["fields"]["level_cols"].join(", ")}</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          Frequency
                        </Heading>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold" >{capitalizeFirstLetter(policy["fields"]["freq"])}</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} width="25%">
                    <Stack>
                      <VStack alignItems="flex-start">
                        <Heading size={{ base: 'sm', md: 'md' }} color="muted">
                          Forecast Horizon
                        </Heading>
                      </VStack>
                      <Stack spacing="4">
                        <Text fontSize="2xl" fontWeight="bold" >{policy["fields"]["fh"]}</Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} width="25%">
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
                </Stack>
              </Box>
              <Box my="1.5rem !important" width="100%">
                <Stack direction="row" divider={<StackDivider />} spacing="0" justifyContent="space-evenly">
                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} width="25%">
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
                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} width="25%">
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
                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} width="25%">
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
                  <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} width="25%">
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

            <Text my="1.5rem !important">The entities have been segmented based on their cumulative AI uplift and <b>{segmentationFactor}</b>. For entities highlighted in green, it is recommended to override the benchmark with the AI forecast. To view the statistics for each entity, click on the corresponding dot.</Text>

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

            <HStack width="100%" justify="space-between" pr="1rem">
              <Text my="1.5rem !important">The entities in this table are sorted from highest uplift to lowest and the policy tracker represents the uplift % for each entity.</Text>
              <Button onClick={() => {
                getAIRecommendationTableApi(true)
              }}>Show all entities</Button>
            </HStack>

            {AIRecommendationTable ? (
              <Box>
                <Accordion allowToggle onChange={(expanded_index: number) => { setExpandedEntityIndex(expanded_index) }}>
                  {AIRecommendationTable["results"].map((entity_data: any, idx: number) => {
                    return (
                      <AccordionItem key={idx}>
                        <h2>
                          <AccordionButton>
                            <HStack as="span" flex='1' textAlign='left'>
                              <Text fontWeight="bold" width="20%" fontSize="large">{entity_data["entity"]}</Text>
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
                                      <Text fontSize="sm">{entity_data["stats"]["pct_change"] > 0 ? "Increase" : "Decrease"} by <b>{Math.abs(entity_data["stats"]["diff"])}</b> from <b>{entity_data["stats"]["last_window__sum"]}</b> over the next {policy["fields"]["fh"]} {FREQDISPLAYMAPPING[policy["fields"]["freq"]]}</Text>
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
                                        <Text color="muted">
                                          Policy Tracker
                                        </Text>
                                        <Stack direction="row" align="baseline">
                                          <Text fontSize="larger" fontWeight="bold">{entity_data["stats"]["score__uplift_pct__rolling_mean"] > 0 ? entity_data["stats"]["score__uplift_pct__rolling_mean"] : 0} %</Text>
                                        </Stack>
                                      </Stack>
                                    </Box>
                                    <Progress value={entity_data["stats"]["score__uplift_pct__rolling_mean"] > 0 ? entity_data["stats"]["score__uplift_pct__rolling_mean"] : 0} size="xs" borderRadius="none" bg="bg-surface" />
                                  </Stack>
                                </HStack>
                                <HStack width="30%" justify="center">
                                  <Button onClick={(e) => {
                                    e.stopPropagation()
                                    chartFilter["entity"] = [entity_data["entity"]]
                                    setChartFilter(chartFilter)
                                    setEntityTrendChart(null)
                                    getEntityTrendChartApi()
                                    onOpenTrendModal()
                                  }}>
                                    View Trend
                                  </Button>
                                </HStack>
                              </HStack>
                            </HStack>
                            <AccordionIcon />
                          </AccordionButton>
                        </h2>
                        <AccordionPanel pb={4}>
                          <TableContainer width="100%" backgroundColor="white">
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