import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  CircularProgress,
  CircularProgressLabel,
  HStack,
  Heading,
  Spinner,
  Stack,
  Tab,
  TabIndicator,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  Tooltip,
  VStack,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import React, { useEffect, useState } from "react";
import { useAuth0AccessToken } from "../../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../../..";
import { getObjective } from "../../../utilities/backend_calls/objective";
import { Objective } from "../objectives_dashboard";
import { useParams } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import ReactEcharts from "echarts-for-react";
import {
  exportAIRecommendationTable,
  getAIRecommendationTable,
} from "../../../utilities/backend_calls/tables";
import { getForecastObjectiveStats } from "../../../utilities/backend_calls/stats";
import { colors } from "../../../theme/theme";
import {
  getRollingForecastChart,
  getSegmentationChart,
  getTrendChart,
} from "../../../utilities/backend_calls/charts";
import {
  faCaretDown,
  faCaretUp,
  faChevronLeft,
  faChevronRight,
} from "@fortawesome/pro-light-svg-icons";
import {
  faArrowUpRightAndArrowDownLeftFromCenter,
  faCircleInfo,
  faFileExport,
} from "@fortawesome/pro-light-svg-icons";
import Toast from "../../../components/toast";
import ExpandedChartModal from "../../../components/expanded_chart_modal";
import InventoryTable from "./_includes/inventory_table";

const FREQDISPLAYMAPPING: Record<string, string> = {
  Hourly: "hourly",
  Daily: "days",
  Weekly: "weeks",
  Monthly: "months",
  Quarterly: "quarters",
  Yearly: "years",
};

const FREQ_TO_SP: Record<string, number> = {
  Hourly: 24,
  Daily: 30,
  Weekly: 52,
  Monthly: 12,
};

const SEGMENTATION_TABS = [
  "volatility",
  "total value",
  "historical growth rate",
  "predicted growth rate",
];

type AIRecommendationTable = Record<string, any>;
type mainStats = Record<string, any>[];

const ForecastObjective = () => {
  const { objective_id } = useParams();
  const [objective, setObjective] = useState<Objective | null>(null);
  const [panelSourceDataFields, setPanelSourceDataFields] = useState<Record<
    string,
    any
  > | null>(null);

  const [mainStats, setMainStats] = useState<mainStats | null>(null);

  const [chartFilter, setChartFilter] = useState<Record<string, string[]>>({});
  const [mainTrendChart, setMainTrendChart] = useState<Record<any, any> | null>(
    null
  );
  const [entityTrendChart, setEntityTrendChart] = useState<Record<
    any,
    any
  > | null>(null);
  const [rollingForecastChart, setRollingForecastChart] = useState<Record<
    any,
    any
  > | null>(null);
  const [segmentationPlot, setSegmentationPlot] = useState<Record<
    any,
    any
  > | null>(null);
  const [segmentationFactor, setSegmentationFactor] = useState("volatility");

  const [AIRecommendationTableFilter, setAIRecommendationTableFilter] =
    useState<Record<string, string[]>>({});
  const [AIRecommendationTable, setAIRecommendationTable] =
    useState<AIRecommendationTable | null>(null);
  const [AIRecommendationTableCache, setAIRecommendationTableCache] = useState<
    Record<number, AIRecommendationTable>
  >({});
  const [
    currentPageAIRecommendationTable,
    setCurrentPageAIRecommendationTable,
  ] = useState<number>(1);
  const [expandedEntityIndex, setExpandedEntityIndex] = useState<number>(0);
  // const [executePlanCustomEntries, setExecutePlanCustomEntries] = useState<Record<string, any>[] | null>(null)
  const [isExportingTable, setIsExportingTable] = useState(false);

  const [expandedChartJSONspec, setExpandedChartJSONspec] = useState<Record<
    any,
    any
  > | null>(null);
  const [expandedChartModalHeader, setExpandedChartModalHeader] = useState("");

  const access_token_indexhub_api = useAuth0AccessToken();
  const user_details = useSelector((state: AppState) => state.reducer?.user);
  const toast = useToast();

  const {
    isOpen: isOpenExpandedChartModal,
    onOpen: onOpenExpandedChartModal,
    onClose: onCloseExpandedChartModal,
  } = useDisclosure();

  const getEntityTrendChartApi = async () => {
    if (objective_id) {
      const entityTrendChart = await getTrendChart(
        objective_id,
        "single_forecast",
        access_token_indexhub_api,
        chartFilter
      );
      setEntityTrendChart(entityTrendChart);
    }
  };

  const getRollingForecastChartApi = async () => {
    if (objective_id) {
      const rollingForecastChart = await getRollingForecastChart(
        objective_id,
        access_token_indexhub_api
      );
      setRollingForecastChart(rollingForecastChart);
    }
  };

  const exportRecommendationTable = async () => {
    if (objective_id && access_token_indexhub_api) {
      setIsExportingTable(true);
      const export_table_response = await exportAIRecommendationTable(
        objective_id,
        null, // to be replaced with executePlanCustomEntries when available
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
      setIsExportingTable(false);
    }
  };

  useEffect(() => {
    const getObjectiveApi = async () => {
      const objective = await getObjective(
        "",
        objective_id,
        access_token_indexhub_api
      );
      objective["objective"]["fields"] = JSON.parse(
        objective["objective"]["fields"]
      );
      setObjective(objective["objective"]);
      setPanelSourceDataFields(objective["panel_source_data_fields"]);
    };

    const getMainTrendChartApi = async () => {
      if (objective_id) {
        const mainTrendChart = await getTrendChart(
          objective_id,
          "single_forecast",
          access_token_indexhub_api
        );
        setMainTrendChart(mainTrendChart);
      }
    };

    const getForecastObjectiveStatsApi = async () => {
      if (objective_id) {
        const forecastObjectiveStats = await getForecastObjectiveStats(
          objective_id,
          access_token_indexhub_api
        );
        setMainStats(forecastObjectiveStats);
      }
    };

    if (access_token_indexhub_api && user_details.id && objective_id) {
      getObjectiveApi();
      getMainTrendChartApi();
      getForecastObjectiveStatsApi();
      getRollingForecastChartApi();
    }
  }, [access_token_indexhub_api, user_details, objective_id]);

  const getAIRecommendationTableApi = async (clear_filter = false) => {
    const filter_by = clear_filter ? {} : AIRecommendationTableFilter;
    setAIRecommendationTable(null);
    const AIRecommendationTable = await getAIRecommendationTable(
      currentPageAIRecommendationTable,
      5,
      objective_id ? objective_id : "",
      access_token_indexhub_api,
      filter_by
    );
    setAIRecommendationTable(AIRecommendationTable);
    AIRecommendationTableCache[currentPageAIRecommendationTable] =
      AIRecommendationTable;
    setAIRecommendationTableCache(AIRecommendationTableCache);
  };

  useEffect(() => {
    if (
      access_token_indexhub_api &&
      objective_id &&
      currentPageAIRecommendationTable
    ) {
      if (
        Object.keys(AIRecommendationTableCache).includes(
          currentPageAIRecommendationTable.toString()
        )
      ) {
        setAIRecommendationTable(
          AIRecommendationTableCache[currentPageAIRecommendationTable]
        );
      } else {
        getAIRecommendationTableApi();
      }
    }
  }, [
    currentPageAIRecommendationTable,
    access_token_indexhub_api,
    objective_id,
  ]);

  useEffect(() => {
    const getSegmentationPlot = async () => {
      if (objective_id) {
        setSegmentationPlot(null);
        const segmentationPlot = await getSegmentationChart(
          objective_id,
          "segment",
          access_token_indexhub_api,
          segmentationFactor
        );
        setSegmentationPlot(segmentationPlot);
      }
    };
    if (access_token_indexhub_api && objective_id && segmentationFactor) {
      getSegmentationPlot();
    }
  }, [segmentationFactor, access_token_indexhub_api, objective_id]);

  useEffect(() => {
    if (AIRecommendationTable && expandedEntityIndex > -1) {
      chartFilter["entity"] = [
        AIRecommendationTable["results"][expandedEntityIndex]["entity"],
      ];
      setChartFilter(chartFilter);
      setEntityTrendChart(null);
      getEntityTrendChartApi();
    }
  }, [expandedEntityIndex, AIRecommendationTable]);

  if (objective && panelSourceDataFields) {
    return (
      <>
        <VStack width="100%" alignItems="flex-start">
          <Heading>AI Forecast</Heading>

          {/* Stats */}
          {objective ? (
            <HStack width="100%">
              <Stack>
                {/* Objective Description */}
                <Text mb="1.5rem !important">
                  {objective["fields"]["description"]}
                </Text>
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
                  <Heading size="md" fontWeight="bold">
                    Predicted Impact
                  </Heading>
                  <Tooltip
                    borderRadius={10}
                    maxW="unset !important"
                    label={
                      <Stack
                        py="0.5rem"
                        direction="row"
                        spacing="0"
                        justifyContent="space-evenly"
                        alignItems="center"
                      >
                        <Box
                          borderRight="1px solid #efeff1"
                          px={{ base: "4", md: "6" }}
                          py="1"
                        >
                          <Stack height="100%">
                            <VStack alignItems="flex-start">
                              <Heading size="sm" color="muted">
                                {mainStats[0]["title"]}
                              </Heading>
                              <Text
                                mt="2px !important"
                                fontSize="3xs"
                                fontWeight="bold"
                                textTransform="uppercase"
                              >
                                {mainStats[0]["subtitle"]}
                              </Text>
                            </VStack>
                            <Stack spacing="4" mt="auto">
                              <Text fontSize="xl" fontWeight="bold">
                                {mainStats[0]["values"]["sum"]} %
                              </Text>
                            </Stack>
                          </Stack>
                        </Box>
                        <Stack>
                          <Box px={{ base: "4", md: "6" }} py="1">
                            <Stack>
                              <VStack alignItems="flex-start">
                                <Heading size="sm" color="muted">
                                  Frequency
                                </Heading>
                                <Text
                                  mt="2px !important"
                                  fontSize="3xs"
                                  fontWeight="bold"
                                  textTransform="uppercase"
                                >
                                  {panelSourceDataFields["freq"]}
                                </Text>
                              </VStack>
                            </Stack>
                          </Box>
                          <Box px={{ base: "4", md: "6" }} py="1">
                            <Stack>
                              <VStack alignItems="flex-start">
                                <Heading size="sm" color="muted">
                                  Forecast Horizon
                                </Heading>
                                <Text
                                  mt="2px !important"
                                  fontSize="3xs"
                                  fontWeight="bold"
                                  textTransform="uppercase"
                                >
                                  {objective["fields"]["fh"]}
                                </Text>
                              </VStack>
                            </Stack>
                          </Box>
                        </Stack>
                      </Stack>
                    }
                    placement="right"
                  >
                    <FontAwesomeIcon icon={faCircleInfo as any} />
                  </Tooltip>
                </HStack>
                <hr></hr>
                <Stack
                  mt="1.5rem"
                  direction="row"
                  spacing="0"
                  justifyContent="space-evenly"
                >
                  <Box px={{ base: "4", md: "6" }} py="1" width="25%">
                    <Stack height="100%">
                      <VStack alignItems="flex-start">
                        <Heading size="sm" color="muted">
                          {mainStats[1]["title"]}
                        </Heading>
                        <Text
                          mt="2px !important"
                          fontSize="3xs"
                          fontWeight="bold"
                          textTransform="uppercase"
                        >
                          {mainStats[1]["subtitle"]}
                        </Text>
                      </VStack>
                      <Stack mt="auto !important">
                        <Text
                          fontSize="3xl"
                          fontWeight="bold"
                          color={
                            mainStats[1]["values"]["pct_change"] > 0
                              ? colors.supplementary.indicators.main_green
                              : colors.supplementary.indicators.main_red
                          }
                        >
                          {mainStats[1]["values"]["sum"]}{" "}
                        </Text>
                        <HStack
                          mt="unset !important"
                          color={
                            mainStats[1]["values"]["pct_change"] > 0
                              ? colors.supplementary.indicators.main_green
                              : colors.supplementary.indicators.main_red
                          }
                        >
                          <Text fontSize="xs">(</Text>
                          <FontAwesomeIcon
                            style={{ marginRight: "3px", marginLeft: "unset" }}
                            icon={
                              mainStats[1]["values"]["pct_change"] > 0
                                ? (faCaretUp as any)
                                : (faCaretDown as any)
                            }
                          />
                          <Text
                            ml="unset !important"
                            fontSize="xs"
                            fontWeight="bold"
                          >
                            {Math.abs(mainStats[1]["values"]["pct_change"])}
                          </Text>
                          <Text fontSize="xs" ml="unset !important">
                            )
                          </Text>
                        </HStack>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: "4", md: "6" }} py="1" width="25%">
                    <Stack height="100%">
                      <VStack alignItems="flex-start">
                        <Heading size="sm" color="muted">
                          {mainStats[2]["title"]}
                        </Heading>
                        <Text
                          mt="2px !important"
                          fontSize="3xs"
                          fontWeight="bold"
                          textTransform="uppercase"
                        >
                          {mainStats[2]["subtitle"]}
                        </Text>
                      </VStack>
                      <Stack mt="auto !important">
                        <Text
                          fontSize="3xl"
                          fontWeight="bold"
                          color={
                            mainStats[2]["values"]["mean_pct"] > 0
                              ? colors.supplementary.indicators.main_green
                              : colors.supplementary.indicators.main_red
                          }
                        >
                          {mainStats[2]["values"]["sum"]}
                        </Text>
                        <HStack
                          mt="unset !important"
                          color={
                            mainStats[2]["values"]["mean_pct"] > 0
                              ? colors.supplementary.indicators.main_green
                              : colors.supplementary.indicators.main_red
                          }
                        >
                          <Text fontSize="xs">(</Text>
                          <FontAwesomeIcon
                            style={{ marginRight: "3px", marginLeft: "unset" }}
                            icon={
                              mainStats[2]["values"]["mean_pct"] > 0
                                ? (faCaretUp as any)
                                : (faCaretDown as any)
                            }
                          />
                          <Text
                            ml="unset !important"
                            fontSize="xs"
                            fontWeight="bold"
                          >
                            {Math.abs(mainStats[2]["values"]["mean_pct"])}
                          </Text>
                          <Text fontSize="xs" ml="unset !important">
                            )
                          </Text>
                        </HStack>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: "4", md: "6" }} py="1" width="25%">
                    <Stack height="100%">
                      <VStack alignItems="flex-start">
                        <Heading size="sm" color="muted">
                          {mainStats[6]["title"]}
                        </Heading>
                        <Text
                          mt="2px !important"
                          fontSize="3xs"
                          fontWeight="bold"
                          textTransform="uppercase"
                        >
                          {mainStats[6]["subtitle"]}
                        </Text>
                      </VStack>
                      <Stack mt="auto !important">
                        <Text fontSize="3xl" fontWeight="bold">
                          {mainStats[6]["values"]["progress"]} %
                        </Text>
                        <Text
                          mt="unset !important"
                          fontSize="xs"
                          fontWeight="bold"
                        >
                          GOAL: {mainStats[5]["values"]["goal"]}%
                        </Text>
                      </Stack>
                    </Stack>
                  </Box>
                  <Box px={{ base: "4", md: "6" }} py="1" width="25%">
                    <Stack height="100%">
                      <VStack alignItems="flex-start">
                        <Heading size="sm" color="muted">
                          {mainStats[4]["title"]}
                        </Heading>
                        <Text
                          mt="2px !important"
                          fontSize="3xs"
                          fontWeight="bold"
                          textTransform="uppercase"
                        >
                          {mainStats[4]["subtitle"]}
                        </Text>
                      </VStack>
                      <Stack mt="auto !important">
                        <Text fontSize="3xl" fontWeight="bold">
                          {mainStats[4]["values"]["n_improvement"]} /{" "}
                          {mainStats[4]["values"]["n_entities"]}
                        </Text>
                        <Text
                          mt="unset !important"
                          fontSize="xs"
                          fontWeight="bold"
                        >
                          {mainStats[7]["values"]["n_achievement"]} HAVE REACHED
                          GOAL
                        </Text>
                      </Stack>
                    </Stack>
                  </Box>
                </Stack>
              </Box>
            </Stack>
          ) : (
            <Stack
              width="100%"
              alignItems="center"
              justifyContent="center"
              height="full"
            >
              <Spinner />
              <Text>Loading...</Text>
            </Stack>
          )}

          {/* Trend Chart */}
          <Box
            my="1.5rem !important"
            width="100%"
            height="27rem"
            p="1rem"
            backgroundColor="white"
            borderRadius="1rem"
          >
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
              <Heading size="md" fontWeight="bold">
                AI Analyst Recommendations
              </Heading>
            </HStack>

            <Text mt="0.5rem !important" mb="1rem" fontSize="sm">
              The entities have been segmented based on their cumulative AI
              uplift and <b>{segmentationFactor}</b>. Entities highlighted in
              green represent recommended focus areas with low volatility and
              high uplift the implementation of AI. To view the statistics for
              each entity, click on the corresponding dot.
            </Text>
            <hr></hr>
            <Tabs
              mt="1.5rem"
              position="relative"
              variant="unstyled"
              isFitted
              isLazy
              lazyBehavior="keepMounted"
              onChange={(index: number) =>
                setSegmentationFactor(SEGMENTATION_TABS[index])
              }
            >
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
            <Box
              my="1.5rem !important"
              width="100%"
              height="27rem"
              p="1rem"
              backgroundColor="white"
              borderRadius="1rem"
            >
              {segmentationPlot ? (
                <ReactEcharts
                  option={segmentationPlot}
                  style={{
                    height: "100%",
                    width: "100%",
                  }}
                  onEvents={{
                    click: (param: any) => {
                      AIRecommendationTableFilter["entity"] = [
                        param["seriesName"],
                      ];
                      setAIRecommendationTableFilter(
                        AIRecommendationTableFilter
                      );
                      getAIRecommendationTableApi();
                    },
                  }}
                />
              ) : (
                <Stack
                  alignItems="center"
                  justifyContent="center"
                  height="full"
                >
                  <Spinner />
                  <Text>Loading...</Text>
                </Stack>
              )}
            </Box>

            <Tabs
              mt="1.5rem"
              position="relative"
              variant="line"
              isLazy
              lazyBehavior="keepMounted"
            >
              <TabList>
                <Tab fontWeight="bold">Forecast Selection</Tab>
                <Tab fontWeight="bold">Inventory Table</Tab>
              </TabList>
              <TabIndicator
                mt="-1.5px"
                height="2px"
                bg="blue.500"
                borderRadius="1px"
              />
              <TabPanels>
                <TabPanel>
                  <>
                    <VStack
                      width="100%"
                      justify="space-between"
                      mb="1rem"
                      mt="1rem"
                      alignItems="flex-start"
                    >
                      <HStack width="100%" justify="space-between">
                        <Text fontSize="sm" width="70%">
                          The entities in this table are sorted from highest
                          uplift to lowest and the objective tracker represents
                          the uplift % for each entity.
                        </Text>
                        <Button
                          size="sm"
                          onClick={() => {
                            getAIRecommendationTableApi(true);
                          }}
                        >
                          Show all entities
                        </Button>
                      </HStack>

                      <Tooltip label="Execute Plan" placement="left">
                        <Button
                          borderRadius="50px"
                          width="60px"
                          height="60px"
                          position="fixed"
                          bottom="50px"
                          right="40px"
                          zIndex="999"
                          backgroundColor="black"
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = "gray";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = "black";
                          }}
                          isLoading={isExportingTable}
                          onClick={() => {
                            exportRecommendationTable();
                          }}
                        >
                          <HStack>
                            <FontAwesomeIcon
                              size="lg"
                              color="white"
                              icon={faFileExport as any}
                            />
                          </HStack>
                        </Button>
                      </Tooltip>
                    </VStack>

                    {AIRecommendationTable ? (
                      <Box>
                        <Accordion
                          allowToggle
                          onChange={(expanded_index: number) => {
                            setExpandedEntityIndex(expanded_index);
                          }}
                        >
                          {AIRecommendationTable["results"].map(
                            (entity_data: any, idx: number) => {
                              return (
                                <AccordionItem key={idx}>
                                  <h2>
                                    <AccordionButton>
                                      <HStack
                                        as="span"
                                        flex="1"
                                        textAlign="left"
                                      >
                                        <VStack
                                          width="20%"
                                          alignItems="flex-start"
                                        >
                                          <Text
                                            pb="1rem"
                                            fontWeight="bold"
                                            fontSize="large"
                                          >
                                            {entity_data["entity"]}
                                          </Text>
                                        </VStack>
                                        <HStack
                                          width="80%"
                                          alignItems="stretch"
                                        >
                                          <Box
                                            px={{ base: "4", md: "6" }}
                                            py={{ base: "5", md: "6" }}
                                            bg="bg-surface"
                                            width={`${100 / 3}%`}
                                          >
                                            <Stack>
                                              <Stack justify="space-between">
                                                <Text
                                                  color="muted"
                                                  fontWeight="bold"
                                                >
                                                  AI Forecast
                                                </Text>
                                                <Text
                                                  color="muted"
                                                  mt="unset !important"
                                                  fontSize="3xs"
                                                  textTransform="uppercase"
                                                  fontWeight="bold"
                                                >
                                                  Over Next{" "}
                                                  {objective["fields"]["fh"]}{" "}
                                                  {
                                                    FREQDISPLAYMAPPING[
                                                      panelSourceDataFields[
                                                        "freq"
                                                      ]
                                                    ]
                                                  }
                                                </Text>
                                              </Stack>
                                              <HStack justify="space-between">
                                                <Text
                                                  fontSize="larger"
                                                  fontWeight="bold"
                                                >
                                                  {
                                                    entity_data["stats"][
                                                      "current_window__stat"
                                                    ]
                                                  }
                                                </Text>

                                                <HStack
                                                  color={
                                                    entity_data["stats"][
                                                      "pct_change"
                                                    ] > 0
                                                      ? colors.supplementary
                                                          .indicators.main_green
                                                      : colors.supplementary
                                                          .indicators.main_red
                                                  }
                                                >
                                                  <Text>(</Text>
                                                  <FontAwesomeIcon
                                                    style={{
                                                      marginRight: "3px",
                                                      marginLeft: "unset",
                                                    }}
                                                    icon={
                                                      entity_data["stats"][
                                                        "pct_change"
                                                      ] > 0
                                                        ? (faCaretUp as any)
                                                        : (faCaretDown as any)
                                                    }
                                                  />
                                                  <Text
                                                    ml="unset !important"
                                                    fontSize="xs"
                                                    fontWeight="bold"
                                                  >
                                                    {Math.abs(
                                                      entity_data["stats"][
                                                        "pct_change"
                                                      ]
                                                    )}
                                                  </Text>
                                                  <Text ml="unset !important">
                                                    )
                                                  </Text>
                                                </HStack>
                                              </HStack>
                                              <Text fontSize="xs">
                                                Predicted to{" "}
                                                {entity_data["stats"][
                                                  "pct_change"
                                                ] >= 0
                                                  ? "increase"
                                                  : "decrease"}{" "}
                                                by{" "}
                                                <b>
                                                  {Math.abs(
                                                    entity_data["stats"]["diff"]
                                                  )}
                                                </b>{" "}
                                                from{" "}
                                                <b>
                                                  {
                                                    entity_data["stats"][
                                                      "last_window__stat"
                                                    ]
                                                  }
                                                </b>{" "}
                                                over the next{" "}
                                                {objective["fields"]["fh"]}{" "}
                                                {
                                                  FREQDISPLAYMAPPING[
                                                    panelSourceDataFields[
                                                      "freq"
                                                    ]
                                                  ]
                                                }
                                              </Text>
                                            </Stack>
                                          </Box>
                                          <Stack
                                            bg="bg-surface"
                                            width={`${100 / 3}%`}
                                            direction="column"
                                            justifyContent="space-between"
                                          >
                                            <Box
                                              px={{ base: "4", md: "6" }}
                                              py={{ base: "5", md: "6" }}
                                            >
                                              <Stack>
                                                <HStack
                                                  justify="space-between"
                                                  alignItems="flex-start"
                                                >
                                                  <Stack>
                                                    <Text
                                                      color="muted"
                                                      fontWeight="bold"
                                                    >
                                                      Objective Tracker
                                                    </Text>
                                                    <Text
                                                      color="muted"
                                                      fontWeight="bold"
                                                      mt="unset !important"
                                                      fontSize="3xs"
                                                      textTransform="uppercase"
                                                    >
                                                      % UPLIFT FOR THE ENTITY
                                                    </Text>
                                                  </Stack>
                                                  <CircularProgress
                                                    capIsRound
                                                    size="3rem"
                                                    value={
                                                      entity_data["stats"][
                                                        "progress"
                                                      ] > 0
                                                        ? entity_data["stats"][
                                                            "progress"
                                                          ]
                                                        : 0
                                                    }
                                                    color="indicator.main_green"
                                                  >
                                                    <CircularProgressLabel fontSize="xs">
                                                      {Math.floor(
                                                        entity_data["stats"][
                                                          "progress"
                                                        ] > 0
                                                          ? entity_data[
                                                              "stats"
                                                            ]["progress"]
                                                          : 0
                                                      )}
                                                      %
                                                    </CircularProgressLabel>
                                                  </CircularProgress>
                                                </HStack>
                                                <VStack align="baseline">
                                                  <Text fontSize="xs">
                                                    AI has made an{" "}
                                                    <b>
                                                      overall progress of{" "}
                                                      {
                                                        entity_data["stats"][
                                                          "progress"
                                                        ]
                                                      }
                                                      %
                                                    </b>{" "}
                                                    towards its goal of{" "}
                                                    {
                                                      entity_data["stats"][
                                                        "goal"
                                                      ]
                                                    }
                                                    %, with an{" "}
                                                    <b>
                                                      average uplift of{" "}
                                                      {
                                                        entity_data["stats"][
                                                          "score__uplift_pct__rolling_mean"
                                                        ]
                                                      }
                                                      %
                                                    </b>{" "}
                                                    over the last{" "}
                                                    {
                                                      FREQ_TO_SP[
                                                        panelSourceDataFields[
                                                          "freq"
                                                        ]
                                                      ]
                                                    }{" "}
                                                    {
                                                      FREQDISPLAYMAPPING[
                                                        panelSourceDataFields[
                                                          "freq"
                                                        ]
                                                      ]
                                                    }
                                                  </Text>
                                                </VStack>
                                              </Stack>
                                            </Box>
                                          </Stack>
                                          <Stack
                                            width={`${100 / 3}%`}
                                            justify="center"
                                          >
                                            <ReactEcharts
                                              option={JSON.parse(
                                                entity_data["sparklines"]
                                              )}
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
                                    <VStack>
                                      <HStack width="100%">
                                        <Box
                                          width="50%"
                                          height="100%"
                                          borderRadius="10"
                                          p="5px"
                                          backgroundColor="white"
                                        >
                                          <HStack
                                            width="100%"
                                            justify="flex-end"
                                          >
                                            <Tooltip
                                              label="Expand Chart"
                                              placement="left"
                                            >
                                              <Button
                                                onClick={() => {
                                                  setExpandedChartJSONspec(
                                                    entityTrendChart
                                                  );
                                                  setExpandedChartModalHeader(
                                                    `Trend (${entity_data["entity"]})`
                                                  );
                                                  onOpenExpandedChartModal();
                                                }}
                                              >
                                                <HStack>
                                                  <FontAwesomeIcon
                                                    icon={
                                                      faArrowUpRightAndArrowDownLeftFromCenter as any
                                                    }
                                                  />
                                                </HStack>
                                              </Button>
                                            </Tooltip>
                                          </HStack>
                                          <Box height="20rem">
                                            {entityTrendChart ? (
                                              <ReactEcharts
                                                option={entityTrendChart}
                                                style={{
                                                  height: "100%",
                                                  width: "100%",
                                                }}
                                              />
                                            ) : (
                                              <Stack
                                                alignItems="center"
                                                borderRadius="10"
                                                justifyContent="center"
                                                height="full"
                                                backgroundColor="white"
                                              >
                                                <Spinner />
                                                <Text>Loading...</Text>
                                              </Stack>
                                            )}
                                          </Box>
                                        </Box>
                                        <Box
                                          width="50%"
                                          height="100%"
                                          borderRadius="10"
                                          p="5px"
                                          backgroundColor="white"
                                        >
                                          <HStack
                                            width="100%"
                                            justify="flex-end"
                                          >
                                            <Tooltip
                                              label="Expand Chart"
                                              placement="left"
                                            >
                                              <Button
                                                onClick={() => {
                                                  setExpandedChartJSONspec(
                                                    rollingForecastChart
                                                      ? JSON.parse(
                                                          rollingForecastChart[
                                                            entity_data[
                                                              "entity"
                                                            ]
                                                          ]
                                                        )
                                                      : null
                                                  );
                                                  setExpandedChartModalHeader(
                                                    `Rolling Forecast (${entity_data["entity"]})`
                                                  );
                                                  onOpenExpandedChartModal();
                                                }}
                                              >
                                                <HStack>
                                                  <FontAwesomeIcon
                                                    icon={
                                                      faArrowUpRightAndArrowDownLeftFromCenter as any
                                                    }
                                                  />
                                                </HStack>
                                              </Button>
                                            </Tooltip>
                                          </HStack>
                                          <Box height="20rem">
                                            {rollingForecastChart ? (
                                              rollingForecastChart[
                                                entity_data["entity"]
                                              ] ? (
                                                <ReactEcharts
                                                  option={JSON.parse(
                                                    rollingForecastChart[
                                                      entity_data["entity"]
                                                    ]
                                                  )}
                                                  style={{
                                                    height: "100%",
                                                    width: "100%",
                                                  }}
                                                />
                                              ) : (
                                                <Stack
                                                  alignItems="center"
                                                  borderRadius="10"
                                                  justifyContent="center"
                                                  height="full"
                                                  backgroundColor="white"
                                                >
                                                  <Text>
                                                    Rolling data not available
                                                    for this objective
                                                  </Text>
                                                </Stack>
                                              )
                                            ) : (
                                              <Stack
                                                alignItems="center"
                                                borderRadius="10"
                                                justifyContent="center"
                                                height="full"
                                                backgroundColor="white"
                                              >
                                                <Spinner />
                                                <Text>Loading...</Text>
                                              </Stack>
                                            )}
                                          </Box>
                                        </Box>
                                      </HStack>
                                    </VStack>
                                  </AccordionPanel>
                                </AccordionItem>
                              );
                            }
                          )}
                        </Accordion>
                        <HStack py="1rem" width="100%" justify="right">
                          <Button
                            onClick={() =>
                              setCurrentPageAIRecommendationTable(
                                currentPageAIRecommendationTable - 1
                              )
                            }
                            colorScheme="blackAlpha"
                            isDisabled={currentPageAIRecommendationTable == 1}
                          >
                            <FontAwesomeIcon icon={faChevronLeft as any} />
                          </Button>
                          <Text>
                            {currentPageAIRecommendationTable}/
                            {AIRecommendationTable["pagination"]["end"]}
                          </Text>
                          <Button
                            onClick={() =>
                              setCurrentPageAIRecommendationTable(
                                currentPageAIRecommendationTable + 1
                              )
                            }
                            colorScheme="blackAlpha"
                            isDisabled={
                              currentPageAIRecommendationTable ==
                              AIRecommendationTable["pagination"]["end"]
                            }
                          >
                            <FontAwesomeIcon icon={faChevronRight as any} />
                          </Button>
                        </HStack>
                      </Box>
                    ) : (
                      <Stack
                        alignItems="center"
                        justifyContent="center"
                        height="full"
                      >
                        <Spinner />
                        <Text>Loading...</Text>
                      </Stack>
                    )}
                  </>
                </TabPanel>
                <TabPanel>
                  {objective_id && (
                    <InventoryTable objective_id={objective_id} />
                  )}
                </TabPanel>
              </TabPanels>
            </Tabs>
          </Box>
        </VStack>

        {expandedChartJSONspec && (
          <ExpandedChartModal
            isOpenExpandedChartModal={isOpenExpandedChartModal}
            onCloseExpandedChartModal={onCloseExpandedChartModal}
            EChartJSONspec={expandedChartJSONspec}
            header={expandedChartModalHeader}
          />
        )}
      </>
    );
  } else {
    return (
      <Stack alignItems="center" justifyContent="center" height="full">
        <Spinner />
        <Text>Loading...</Text>
      </Stack>
    );
  }
};

export default ForecastObjective;
