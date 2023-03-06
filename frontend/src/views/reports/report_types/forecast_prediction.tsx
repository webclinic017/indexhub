import React, { useState, useEffect } from "react";
import {
  getChart,
  getLevelsData,
  getReport,
  getTable,
} from "../../../utilities/backend_calls/report";
import { useAuth0AccessToken } from "../../../utilities/hooks/auth0";
import {
  VStack,
  HStack,
  Text,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SliderMark,
  Container,
  Stack,
  Box,
  Heading,
  FormControl,
  FormLabel,
  CircularProgressLabel,
  CircularProgress,
  StackDivider,
  SimpleGrid,
  useColorModeValue,
} from "@chakra-ui/react";
import ReactEcharts from "echarts-for-react";
import { Report } from "../reports";
import { useParams } from "react-router-dom";
import { Select } from "chakra-react-select";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowDown, faArrowUp } from "@fortawesome/free-solid-svg-icons";
import { colors } from "../../../theme/theme";
import List from "../../../components/list";
import { roundToTwoDecimalPlaces } from "../../../utilities/helpers";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const backtest_type_readable_names: any = {
  mae: "MAE",
  overforecast: "Over-Forecast",
  underforecast: "Under-Forecast",
};

const backtest_type_options = [
  {
    value: "mae",
    label: "MAE",
  },
  {
    value: "overforecast",
    label: "Over-Forecast",
  },
  {
    value: "underforecast",
    label: "Under-Forecast",
  },
];

const backtest_sort_options = [
  {
    value: ":manual",
    label: "Benchmark",
  },
  {
    value: ":forecast",
    label: "AI",
  },
  {
    value: "_improvement",
    label: "Uplift",
  },
  {
    value: "_improvement_%",
    label: "Uplift %",
  },
];

export type chartData = {
  chart_id: string;
  title: string;
  chart_type: string;
  readable_names: Record<string, never>;
  chart_data: Record<string, never>;
};

type Forecast_Recommendations_Table = {
  month_year: string;
  rpt_forecast_10: string;
  rpt_forecast_30: string;
  rpt_forecast_50: string;
  rpt_forecast_70: string;
  rpt_forecast_90: string;
};

export type forecastRecommendationsTable = {
  readable_names: Record<string, never>;
  data: Forecast_Recommendations_Table[];
  title: string;
};

const initFilters = (report_filters: string[] = []) => {
  const filters_init: Record<string, any[]> = {}; // eslint-disable-line @typescript-eslint/no-explicit-any
  if (report_filters.length > 0) {
    report_filters.forEach((_, idx) => {
      filters_init[`entity_${idx}`] = [];
    });
  }

  filters_init["quantile"] = [0.5];
  return filters_init;
};

export default function Forecast_Recommendations() {
  const getChartByChartId = async () => {
    const chart_response = await getChart(
      String(params.id),
      "forecast_recommendation",
      access_token_indexhub_api,
      filters
    );
    setChartData(chart_response);
  };

  const getTableByTableId = async () => {
    const table_response = await getTable(
      String(params.id),
      "forecast_recommendation",
      access_token_indexhub_api,
      filters
    );
    console.log(table_response.forecast_recommendations);
    setTableData(table_response.forecast_recommendations);
    const backtests_table_response = await getTable(
      String(params.id),
      "backtests",
      access_token_indexhub_api,
      filters
    );
    console.log(backtests_table_response.backtests);
    setBacktestsTableData(backtests_table_response.backtests);
  };

  const params = useParams();
  const [selectedReport, setSelectedReport] = useState<Report>({
    id: "",
    source_id: "",
    source_name: "",
    entities: {},
    target_col: "",
    level_cols: [],
    user_id: "",
    chart_id: "",
    table_id: "",
    status: "",
    created_at: "",
    completed_at: "",
  });
  const [chartData, setChartData] = useState<chartData>({
    chart_id: "",
    title: "",
    chart_type: "",
    readable_names: {},
    chart_data: {},
  });
  const [tableData, setTableData] = useState<forecastRecommendationsTable>({
    readable_names: {},
    data: [
      {
        month_year: "",
        rpt_forecast_10: "",
        rpt_forecast_30: "",
        rpt_forecast_50: "",
        rpt_forecast_70: "",
        rpt_forecast_90: "",
      },
    ],
    title: "",
  });
  const [backtestsTableData, setBacktestsTableData] = useState<
    Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
  >({
    readable_names: {},
    data: [
      {
        month_year: "",
        rpt_forecast_10: "",
        rpt_forecast_30: "",
        rpt_forecast_50: "",
        rpt_forecast_70: "",
        rpt_forecast_90: "",
      },
    ],
    title: "",
  });
  const [filters, setFilters] = useState<Record<string, any[]>>(initFilters()); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [levelsData, setLevelsData] = useState<Record<string, any>>({}); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [backtestType, setBacktestType] = useState("mae");
  const [backtestSortBy, setBacktestSortBy] = useState(":manual");
  const access_token_indexhub_api = useAuth0AccessToken();

  useEffect(() => {
    const getReportByReportId = async () => {
      const reports_response = await getReport(
        "",
        params.id,
        access_token_indexhub_api
      );
      setSelectedReport(reports_response.reports[0]);
      setFilters(initFilters(reports_response.reports[0].level_cols));

      const levels_data_response = await getLevelsData(
        params.id,
        access_token_indexhub_api
      );
      console.log(levels_data_response);
      setLevelsData(levels_data_response.levels_data);
    };
    if (access_token_indexhub_api) {
      getReportByReportId();
    }
  }, [access_token_indexhub_api]);

  useEffect(() => {
    console.log(levelsData);
  }, [levelsData]);

  useEffect(() => {
    if (access_token_indexhub_api && selectedReport.id) {
      const filters_init: Record<string, any[]> = {}; // eslint-disable-line @typescript-eslint/no-explicit-any
      selectedReport?.level_cols.forEach((_, idx) => {
        filters_init[`entity_${idx}`] = [];
      });
      filters_init["quantile"] = [0.5];
      setFilters(filters_init);

      getChartByChartId();
      getTableByTableId();
    }
  }, [access_token_indexhub_api, selectedReport.id]);

  const sliderLabelStyles = {
    mt: "2",
    ml: "-2.5",
    fontSize: "sm",
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const updateFilter = (entity: string, value: any, is_multiple = true) => {
    let choices = filters[entity];
    const filters_internal = JSON.parse(JSON.stringify(filters));

    if (is_multiple) {
      const index = choices.indexOf(value);
      if (index > -1) {
        // only splice array when item is found
        choices.splice(index, 1); // 2nd parameter means remove one item only
      } else {
        choices.push(value);
      }
    } else {
      choices = [value];
    }
    filters_internal[entity] = choices;
    setFilters(filters_internal);
  };

  React.useEffect(() => {
    console.log(filters);
    if (access_token_indexhub_api) {
      getChartByChartId();
      getTableByTableId();
    }
  }, [filters]);

  const option = {
    tooltip: {
      trigger: "axis",
    },
    legend: {
      data: Object.values(chartData.readable_names),
      right: 2,
    },
    grid: {
      left: "0",
      right: "0",
      bottom: "3%",
      containLabel: true,
    },
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: "none",
        },
        saveAsImage: {},
      },
      left: 2,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: chartData.chart_data.time,
    },
    yAxis: {
      type: "value",
    },
    dataZoom: [
      {
        type: "inside",
        start: 0,
      },
      {
        start: 0,
      },
    ],
    series: [
      {
        name: chartData.readable_names.rpt_actual,
        type: chartData.chart_type,
        stack: chartData.readable_names.rpt_actual,
        data: chartData.chart_data.rpt_actual,
      },
      {
        name: chartData.readable_names.rpt_manual,
        type: chartData.chart_type,
        stack: chartData.readable_names.rpt_manual,
        data: chartData.chart_data.rpt_manual,
      },
      {
        name: chartData.readable_names.rpt_forecast,
        type: chartData.chart_type,
        stack: chartData.readable_names.rpt_forecast,
        data: chartData.chart_data.rpt_forecast,
      },
    ],
  };

  const rpt_forecast_key = `rpt_forecast_${Math.round(
    filters["quantile"][0] * 100
  )}`;

  const report_stats = {
    forecast_horizon: 0,
    mae_uplift_percentage: [0, 0],
  };
  report_stats["forecast_horizon"] = tableData.data.length;
  report_stats["mae_uplift_percentage"] = [
    backtestsTableData["data"]
      .map((item: any) => item["mae_improvement"]) // eslint-disable-line @typescript-eslint/no-explicit-any
      .reduce((prev: number, next: number) => prev + next),
    backtestsTableData["data"]
      .map((item: any) => item["mae_improvement_%"]) // eslint-disable-line @typescript-eslint/no-explicit-any
      .reduce((prev: number, next: number) => prev + next) /
      backtestsTableData["data"].length,
  ];

  console.log(report_stats);

  if (selectedReport.id != "") {
    return (
      <VStack padding="10px">
        <Text width="90vw" textAlign="left" fontSize="2xl" fontWeight="bold">
          Forecast Recommendations
        </Text>
        <VStack>
          <HStack
            width="90vw"
            justify="space-between"
            alignItems="center"
            pt="1rem"
          >
            <VStack
              width="48%"
              alignItems="flex-start"
              paddingInline="20px"
              padding="unset"
            >
              <Container margin="1rem 0 4rem" maxWidth="unset">
                <SimpleGrid columns={2} gap={{ base: "5", md: "6" }}>
                  <Box
                    bg="bg-surface"
                    boxShadow={useColorModeValue("sm", "sm-dark")}
                  >
                    <Box
                      px={{ base: "4", md: "6" }}
                      py={{ base: "5", md: "6" }}
                    >
                      <Stack>
                        <Text fontSize="lg" fontWeight="medium">
                          Total MAE Uplift (%)
                        </Text>
                        <Heading
                          color={
                            report_stats.mae_uplift_percentage[0] > 0
                              ? "indicator.main_green"
                              : "indicator.main_red"
                          }
                          size="lg"
                        >
                          {roundToTwoDecimalPlaces(
                            report_stats.mae_uplift_percentage[0]
                          )}{" "}
                          (
                          {roundToTwoDecimalPlaces(
                            report_stats.mae_uplift_percentage[1]
                          )}
                          %)
                        </Heading>
                      </Stack>
                    </Box>
                  </Box>
                  <Box
                    bg="bg-surface"
                    boxShadow={useColorModeValue("sm", "sm-dark")}
                  >
                    <Box
                      px={{ base: "4", md: "6" }}
                      py={{ base: "5", md: "6" }}
                    >
                      <Stack>
                        <Text fontSize="lg" fontWeight="medium">
                          Forecast Horizon
                        </Text>
                        <Heading size="lg">
                          {report_stats.forecast_horizon}
                        </Heading>
                      </Stack>
                    </Box>
                  </Box>
                </SimpleGrid>
              </Container>
              <Text textAlign="left" fontSize="lg" fontWeight="bold">
                AI Forecast Adjustment:
              </Text>
              <Text textAlign="left" fontSize="sm">
                Subtitle for the quantile slider here
              </Text>
              <Container
                marginTop="3rem !important"
                justifyContent="center"
                alignItems="center"
                display="flex"
                height="100%"
                flexDirection="column"
                maxWidth="unset"
              >
                <Slider
                  defaultValue={0.5}
                  min={0.1}
                  max={0.9}
                  step={0.05}
                  aria-label="slider-ex-6"
                  onChange={(val) => updateFilter("quantile", val, false)}
                >
                  <SliderMark value={0.1} {...sliderLabelStyles}>
                    Under
                  </SliderMark>
                  <SliderMark value={0.5} {...sliderLabelStyles}>
                    Balanced
                  </SliderMark>
                  <SliderMark value={0.9} {...sliderLabelStyles}>
                    Over
                  </SliderMark>
                  <SliderMark
                    value={filters["quantile"][0]}
                    textAlign="center"
                    color={
                      filters["quantile"][0] < 0.5
                        ? "indicator.main_red"
                        : "indicator.main_green"
                    }
                    mt="-10"
                    ml="-5"
                    w="12"
                  >
                    {Math.floor(((filters["quantile"][0] - 0.5) / 0.4) * 100)}%
                  </SliderMark>
                  <SliderTrack backgroundColor="indicator.main_green">
                    <SliderFilledTrack backgroundColor="indicator.main_red" />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </Container>
            </VStack>
            <HStack width="48%" justifyContent="flex-start" overflowX="scroll">
              {Object.keys(levelsData).map((level, idx) => {
                return (
                  <List
                    data={levelsData[level]}
                    title={`All ${selectedReport.level_cols[idx]}(s)`}
                    subtitle={`Choose your preferred ${selectedReport.level_cols[idx]}(s) you would like to filter with (multiple choices)`}
                    entity={level}
                    state={filters}
                    stateSetter={updateFilter}
                    minWidth="25rem"
                    key={idx}
                  ></List>
                );
              })}
            </HStack>
          </HStack>

          <VStack alignItems="flex-start" width="90vw">
            <Container maxWidth="unset" py={{ base: "16", md: "24" }}>
              <Stack spacing={{ base: "12", md: "16" }}>
                <Stack spacing={{ base: "4", md: "6" }}>
                  <Stack
                    spacing={{ base: "4", md: "5" }}
                    textAlign="center"
                    align="center"
                  >
                    <Heading size={{ base: "sm", md: "md" }}>
                      AI Forecast
                    </Heading>
                    <Text
                      fontSize={{ base: "lg", md: "xl" }}
                      color="muted"
                      maxW="3xl"
                    >
                      Here&apos;s what the forecast looks like based on the risk
                      metric you have chosen above.
                    </Text>
                  </Stack>
                </Stack>
                <Stack
                  overflowX="scroll"
                  direction="row"
                  spacing={{ base: "8", md: "4" }}
                  {...{ divider: <StackDivider /> }}
                >
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {tableData.data.map((item: any, idx) => {
                    let prev_forecast_value = 0;
                    if (idx > 0) {
                      prev_forecast_value = (tableData.data[idx - 1] as any)[ // eslint-disable-line @typescript-eslint/no-explicit-any
                        rpt_forecast_key
                      ];
                    }
                    const current_forecast_value = item[rpt_forecast_key];
                    return (
                      <Box
                        key={idx}
                        px={{ md: "6" }}
                        pt={{ base: "4", md: "0" }}
                      >
                        <Stack spacing="5">
                          <Stack spacing="1">
                            <HStack>
                              <VStack>
                                <Text
                                  color="muted"
                                  fontSize="lg"
                                  fontWeight="medium"
                                >
                                  {item.month_year}
                                </Text>
                                <Heading
                                  size="lg"
                                  color={
                                    idx > 0
                                      ? current_forecast_value >
                                        prev_forecast_value
                                        ? "indicator.main_green"
                                        : "indicator.main_red"
                                      : "accent"
                                  }
                                >
                                  {Math.round(
                                    (current_forecast_value + Number.EPSILON) *
                                      100
                                  ) / 100}
                                </Heading>
                              </VStack>
                              <Stack justify="center">
                                {idx > 0 ? (
                                  <HStack ml="1rem">
                                    <FontAwesomeIcon
                                      icon={
                                        current_forecast_value >
                                        prev_forecast_value
                                          ? faArrowUp
                                          : faArrowDown
                                      }
                                      color={
                                        current_forecast_value >
                                        prev_forecast_value
                                          ? colors.supplementary.indicators
                                              .main_green
                                          : colors.supplementary.indicators
                                              .main_red
                                      }
                                    />
                                    <Text
                                      color={
                                        current_forecast_value >
                                        prev_forecast_value
                                          ? "indicator.main_green"
                                          : "indicator.main_red"
                                      }
                                      fontSize="lg"
                                      fontWeight="medium"
                                    >
                                      {Math.round(
                                        (Math.abs(
                                          ((current_forecast_value -
                                            prev_forecast_value) /
                                            prev_forecast_value) *
                                            100
                                        ) +
                                          Number.EPSILON) *
                                          100
                                      ) / 100}
                                      %
                                    </Text>
                                  </HStack>
                                ) : (
                                  <></>
                                )}
                              </Stack>
                            </HStack>
                          </Stack>
                        </Stack>
                      </Box>
                    );
                  })}
                </Stack>
              </Stack>
            </Container>
          </VStack>

          <Text width="90vw" textAlign="left" fontSize="xl" fontWeight="bold">
            Forecast Prediction
          </Text>
          <Text width="90vw" textAlign="left" fontSize="sm">
            Actual, Benchmark and AI Forecast over time
          </Text>
          <ReactEcharts
            option={option}
            style={{
              height: "17.5rem",
              width: "100%",
              margin: "2rem 0",
            }}
          />
        </VStack>

        <VStack width="100%" py={{ base: "4", md: "8" }}>
          <Stack
            spacing={{ base: "4", md: "5" }}
            textAlign="center"
            align="center"
            mb="3rem"
          >
            <Heading size={{ base: "sm", md: "md" }}>Backtest Result</Heading>
            <Text fontSize={{ base: "lg", md: "xl" }} color="muted" maxW="3xl">
              Here&apos;s what the backtest result looks like based on the risk
              metric you have chosen above.
            </Text>
          </Stack>
          <Stack spacing="5" flex="1" width="full">
            <VStack>
              <HStack width="60%" mb="2rem">
                <FormControl isRequired>
                  <FormLabel>
                    <b>Backtest Score</b>
                  </FormLabel>
                  <Select
                    options={backtest_type_options}
                    onChange={(value) =>
                      setBacktestType(value ? value.value : "")
                    }
                    useBasicStyles
                  />
                </FormControl>
                <FormControl isRequired>
                  <FormLabel>
                    <b>Sort By</b>
                  </FormLabel>
                  <Select
                    options={backtest_sort_options}
                    onChange={(value) =>
                      setBacktestSortBy(value ? value.value : "")
                    }
                    useBasicStyles
                  />
                </FormControl>
              </HStack>
              <Stack spacing="3" width="full">
                {backtestsTableData.data
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  .sort((a: any, b: any) => {
                    a[`${backtestType}${backtestSortBy}`] -
                      b[`${backtestType}${backtestSortBy}`];
                  })
                  .map(
                    (
                      item: any, // eslint-disable-line @typescript-eslint/no-explicit-any
                      idx: number
                    ) =>
                      item ? (
                        <Box
                          key={idx}
                          bg="lists.bg_grey"
                          pl="1rem"
                          boxShadow="sm"
                          position="relative"
                          borderRadius="lg"
                        >
                          <Stack shouldWrapChildren spacing="4">
                            <HStack justify="space-around">
                              <Text
                                width="15%"
                                fontSize="sm"
                                fontWeight="medium"
                                color="emphasized"
                              >
                                <b>{item["entity_0"]}</b>
                              </Text>
                              <VStack width="85%">
                                <HStack
                                  width="full"
                                  justify="flex-start"
                                  backgroundColor="lists.bg_light_grey"
                                  p="0.5rem 0 0.5rem 1rem"
                                  borderTopRightRadius="lg"
                                >
                                  <Text width="20%" fontSize="xs">
                                    <b>Action:</b>{" "}
                                    {item[`${backtestType}_improvement`] > 0
                                      ? "✅ Use AI predictions"
                                      : "⏸ Use benchmark"}
                                  </Text>
                                  <Text width="40%" fontSize="xs">
                                    <b>Explanation:</b>{" "}
                                    {item[`${backtestType}_improvement`] > 0
                                      ? `AI has higher ${backtest_type_readable_names[backtestType]} then benchmark`
                                      : `AI has lower ${backtest_type_readable_names[backtestType]} then benchmark`}
                                  </Text>
                                </HStack>
                                <HStack width="full" justify="center">
                                  <VStack width="20%" alignItems="flex-start">
                                    <Text
                                      fontSize="xs"
                                      color="subtle"
                                      fontWeight="medium"
                                    >
                                      {
                                        backtest_type_readable_names[
                                          backtestType
                                        ]
                                      }{" "}
                                      (Benchmark)
                                    </Text>
                                    <Text
                                      fontSize="lg"
                                      color="subtle"
                                      fontWeight="bold"
                                    >
                                      {Math.round(
                                        (item[`${backtestType}:manual`] +
                                          Number.EPSILON) *
                                          100
                                      ) / 100}
                                    </Text>
                                  </VStack>
                                  <VStack width="20%" alignItems="flex-start">
                                    <Text
                                      fontSize="xs"
                                      color="subtle"
                                      fontWeight="medium"
                                    >
                                      {
                                        backtest_type_readable_names[
                                          backtestType
                                        ]
                                      }{" "}
                                      (AI)
                                    </Text>
                                    <Text
                                      fontSize="lg"
                                      color="subtle"
                                      fontWeight="bold"
                                    >
                                      {Math.round(
                                        (item[`${backtestType}:forecast`] +
                                          Number.EPSILON) *
                                          100
                                      ) / 100}
                                    </Text>
                                  </VStack>
                                  <VStack width="20%" alignItems="flex-start">
                                    <Text
                                      fontSize="xs"
                                      color="subtle"
                                      fontWeight="medium"
                                    >
                                      {
                                        backtest_type_readable_names[
                                          backtestType
                                        ]
                                      }{" "}
                                      (Uplift)
                                    </Text>
                                    <Text
                                      fontSize="lg"
                                      color="subtle"
                                      fontWeight="bold"
                                    >
                                      {Math.round(
                                        (item[`${backtestType}_improvement`] +
                                          Number.EPSILON) *
                                          100
                                      ) / 100}
                                    </Text>
                                  </VStack>
                                  <VStack width="20%" alignItems="flex-start">
                                    <Text
                                      fontSize="xs"
                                      color="subtle"
                                      fontWeight="medium"
                                    >
                                      {
                                        backtest_type_readable_names[
                                          backtestType
                                        ]
                                      }{" "}
                                      (Uplift %)
                                    </Text>
                                    <CircularProgress
                                      value={Math.abs(
                                        item[`${backtestType}_improvement_%`]
                                      )}
                                      color={
                                        item[`${backtestType}_improvement_%`] >
                                        0
                                          ? "indicator.green_2"
                                          : "indicator.red_2"
                                      }
                                    >
                                      <CircularProgressLabel>
                                        {Math.round(
                                          (item[
                                            `${backtestType}_improvement_%`
                                          ] +
                                            Number.EPSILON) *
                                            100
                                        ) / 100}
                                      </CircularProgressLabel>
                                    </CircularProgress>
                                  </VStack>
                                </HStack>
                              </VStack>
                            </HStack>
                          </Stack>
                        </Box>
                      ) : null
                  )}
              </Stack>
            </VStack>
          </Stack>
        </VStack>
      </VStack>
    );
  } else {
    return <></>;
  }
}
