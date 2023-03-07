import React, { useState, useEffect } from "react";
import {
  getChart,
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
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Button,
  Image,
} from "@chakra-ui/react";
import ReactEcharts from "echarts-for-react";
import { Report } from "../reports";
import { useParams } from "react-router-dom";
import { Select } from "chakra-react-select";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowDown, faArrowUp } from "@fortawesome/free-solid-svg-icons";
import { colors } from "../../../theme/theme";
import {
  capitalizeFirstLetter,
  roundToTwoDecimalPlaces,
} from "../../../utilities/helpers";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const getSearchOptions = (data: Record<any, any>[]) => {
  const options: Record<any, string>[] = []; // eslint-disable-line @typescript-eslint/no-explicit-any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data.map((item: any) => {
    options.push({
      value: item["entity_0"],
      label: `Territory:${item["entity_0"]}`,
    });
  });
  return options;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const backtest_type_readable_names: any = {
  mae: "MAE",
  overforecast: "Over-Forecast",
  underforecast: "Under-Forecast",
};

const backtest_sort_options = [
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
      { quantile: filters["quantile"] }
    );
    setChartData(chart_response);
  };

  const getFilteredChartByChartId = async () => {
    const chart_response = await getChart(
      String(params.id),
      "forecast_recommendation",
      access_token_indexhub_api,
      filters
    );
    setFilteredChartData(chart_response);
  };

  const getTableByTableId = async () => {
    const table_response = await getTable(
      String(params.id),
      "forecast_recommendation",
      access_token_indexhub_api,
      filters
    );
    setTableData(table_response.forecast_recommendations);
    const backtests_table_response = await getTable(
      String(params.id),
      "backtests",
      access_token_indexhub_api,
      { quantile: filters["quantile"] }
    );
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
  const [filteredChartData, setFilteredChartData] = useState<chartData>({
    chart_id: "",
    title: "",
    chart_type: "",
    readable_names: {},
    chart_data: {},
  });
  const [showFilteredChartData, setShowFilteredChartData] = useState(false);
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
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    Record<string, any>
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
  // const [levelsData, setLevelsData] = useState<Record<string, any>>({}) // eslint-disable-line @typescript-eslint/no-explicit-any
  const [backtestType] = useState("mae");
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

      // const levels_data_response = await getLevelsData(params.id, access_token_indexhub_api)
      // setLevelsData(levels_data_response.levels_data)
    };
    if (access_token_indexhub_api) {
      getReportByReportId();
    }
  }, [access_token_indexhub_api]);

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
    if (access_token_indexhub_api) {
      getFilteredChartByChartId();
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
        itemStyle: { color: "#194fdc" },
      },
      {
        name: chartData.readable_names.rpt_manual,
        type: chartData.chart_type,
        stack: chartData.readable_names.rpt_manual,
        data: chartData.chart_data.rpt_manual,
        itemStyle: { color: "#B7B7B7" },
      },
      {
        name: chartData.readable_names.rpt_forecast,
        type: chartData.chart_type,
        stack: chartData.readable_names.rpt_forecast,
        data: chartData.chart_data.rpt_forecast,
        itemStyle: { color: "#B79320" },
      },
    ],
  };

  const filtered_chart_option = {
    tooltip: {
      trigger: "axis",
    },
    legend: {
      data: Object.values(filteredChartData.readable_names),
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
      data: filteredChartData.chart_data.time,
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
        name: filteredChartData.readable_names.rpt_actual,
        type: filteredChartData.chart_type,
        stack: filteredChartData.readable_names.rpt_actual,
        data: filteredChartData.chart_data.rpt_actual,
        itemStyle: { color: "#194fdc" },
      },
      {
        name: filteredChartData.readable_names.rpt_manual,
        type: filteredChartData.chart_type,
        stack: filteredChartData.readable_names.rpt_manual,
        data: filteredChartData.chart_data.rpt_manual,
        itemStyle: { color: "#B7B7B7" },
      },
      {
        name: filteredChartData.readable_names.rpt_forecast,
        type: filteredChartData.chart_type,
        stack: filteredChartData.readable_names.rpt_forecast,
        data: filteredChartData.chart_data.rpt_forecast,
        itemStyle: { color: "#B79320" },
      },
    ],
  };

  // const rpt_forecast_key = `rpt_forecast_${Math.round(filters["quantile"][0] * 100)}`

  const report_stats = {
    forecast_horizon: 0,
    mae_uplift_percentage: [0, 0],
    mae_forecast: 0,
    mae_manual: 0,
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
  report_stats["mae_forecast"] = backtestsTableData["data"]
    .map((item: any) => item["mae:forecast"]) // eslint-disable-line @typescript-eslint/no-explicit-any
    .reduce((prev: number, next: number) => prev + next);
  report_stats["mae_manual"] = backtestsTableData["data"]
    .map((item: any) => item["mae:manual"]) // eslint-disable-line @typescript-eslint/no-explicit-any
    .reduce((prev: number, next: number) => prev + next);

  if (selectedReport.id != "") {
    return (
      <VStack padding="10px">
        <VStack width="100%">
          <Text fontSize="3xl" width="100%" fontWeight="bold">
            Forecast Recommendation
          </Text>
          <HStack width="100%" justify="left">
            <Button colorScheme="facebook">Export to PDF</Button>
            <Button colorScheme="facebook">Export to Excel</Button>
          </HStack>
          <HStack width="100%">
            <VStack width="100%" alignItems="left">
              <Text fontSize="lg" fontWeight="bold">
                Recommendation:
              </Text>
              <Text>
                Using the AI forecasts is predicted to have an overall
                improvement of{" "}
                <b>
                  {roundToTwoDecimalPlaces(
                    report_stats["mae_uplift_percentage"][1]
                  )}
                  %
                </b>{" "}
                across {backtestsTableData.data.length}{" "}
                {selectedReport.level_cols[0]}. AI forecasts outperform the
                manual forecasts by a <b>significant</b> margin for{" "}
                <b>
                  3 out of {backtestsTableData.data.length}{" "}
                  {selectedReport.level_cols[0]}
                </b>
                . The manual forecasts have an overall forecast error (MAE) of{" "}
                <b>{roundToTwoDecimalPlaces(report_stats["mae_manual"])}</b>{" "}
                while the AI forecasts have a lower forecast error (MAE) of{" "}
                <b>{roundToTwoDecimalPlaces(report_stats["mae_forecast"])}</b>{" "}
                for {backtestsTableData.data.length}{" "}
                {selectedReport.level_cols[0]}. The top 5{" "}
                {selectedReport.level_cols[0]} to investigate are
                Tasmania(28.63% predicted uplift), Queensland(25.03% predicted
                uplift), Canberra(19.4% predicted uplift), West Australia(13.1%
                predicted uplift), Victoria(10.4% predicted uplift).
              </Text>
            </VStack>
          </HStack>
          <HStack width="100%" alignItems="flex-start">
            <VStack width="60%">
              <Container margin="1rem 0" maxWidth="unset">
                <SimpleGrid columns={3} gap={{ base: "5", md: "6" }}>
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
                          size="md"
                          color={
                            report_stats.mae_uplift_percentage[0] > 0
                              ? "indicator.main_green"
                              : "indicator.main_red"
                          }
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
                        <Heading size="md">
                          {report_stats.forecast_horizon}
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
                          Frequency
                        </Text>
                        <Heading size="md">Monthly</Heading>
                      </Stack>
                    </Box>
                  </Box>
                </SimpleGrid>
              </Container>
              <VStack width="100%" alignItems="left">
                <Text fontSize="lg" fontWeight="bold">
                  AI Forecast Adjustment:
                </Text>
                <Text fontSize="sm">
                  The AI Forecast provides{" "}
                  {filters["quantile"][0] == 0.5
                    ? "balanced"
                    : filters["quantile"][0] > 0.5
                    ? "over"
                    : "under"}{" "}
                  forecasts where forecast values are predicted to be higher
                  than the actual values{" "}
                  {roundToTwoDecimalPlaces(filters["quantile"][0] * 100)}% of
                  the time.
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
                          ? "indicator.main_blue"
                          : "indicator.main_green"
                      }
                      mt="-10"
                      ml="-5"
                      w="12"
                    >
                      {Math.floor(((filters["quantile"][0] - 0.5) / 0.4) * 100)}
                      %
                    </SliderMark>
                    <SliderTrack backgroundColor="indicator.main_green">
                      <SliderFilledTrack backgroundColor="indicator.main_blue" />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                </Container>
              </VStack>
              <ReactEcharts
                option={option}
                style={{
                  height: "17.5rem",
                  width: "100%",
                  margin: "6rem 0 2rem",
                }}
              />

              <FormControl>
                <FormLabel textAlign="left">
                  <b>Search</b>
                </FormLabel>
                <Select
                  options={getSearchOptions(backtestsTableData.data)}
                  onChange={(value) => {
                    if (value) {
                      updateFilter("entity_0", value.value, false);
                      setShowFilteredChartData(true);
                    }
                  }}
                  useBasicStyles
                />
              </FormControl>
              <VStack
                justify="center"
                height="30rem"
                width="100%"
                backgroundColor="#f7fafc"
                borderRadius="8px"
                p="1rem"
              >
                {showFilteredChartData ? (
                  <>
                    <ReactEcharts
                      option={filtered_chart_option}
                      style={{
                        height: "17.5rem",
                        width: "100%",
                        margin: "2rem 0",
                      }}
                    />
                    <Text>
                      Territory:{filters["entity_0"][0]} is trending upwards
                      since 2022/09/01 and is expected to increase by 20.12% for
                      the next 8 Months. Significant variability of manual
                      forecast is observed on 2021/01/01 where the forecast
                      error is -606%. Backtests using AI forecast exhibits
                      28.63% improvement over benchmarks.
                    </Text>
                  </>
                ) : (
                  <Text>Explore AI backtests and forecasts by entity</Text>
                )}
              </VStack>
            </VStack>

            <VStack width="40%" px="4">
              <Box bg="bg-surface" py="4">
                <FormControl
                  borderBottom="1px solid #c6c9cc"
                  pb="1rem"
                  mb="1rem"
                >
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
                <Stack divider={<StackDivider />} spacing="4">
                  {backtestsTableData.data
                    .sort(
                      (
                        a: any, // eslint-disable-line @typescript-eslint/no-explicit-any
                        b: any // eslint-disable-line @typescript-eslint/no-explicit-any
                      ) =>
                        b[`${backtestType}${backtestSortBy}`] -
                        a[`${backtestType}${backtestSortBy}`]
                    )
                    ?.map(
                      (
                        item: any // eslint-disable-line @typescript-eslint/no-explicit-any
                      ) => (
                        <Stack
                          key={item["entity_0"]}
                          fontSize="sm"
                          spacing="0.5"
                        >
                          <HStack justify="space-between">
                            <Text fontWeight="bold" color="emphasized">
                              {`${capitalizeFirstLetter(
                                selectedReport.level_cols[0]
                              )}:${item["entity_0"]}`}
                            </Text>
                            <HStack>
                              <FontAwesomeIcon
                                icon={
                                  item["mae_improvement_%"] < 0
                                    ? faArrowDown
                                    : faArrowUp
                                }
                                color={
                                  item["mae_improvement_%"] < 0
                                    ? colors.supplementary.indicators.main_red
                                    : colors.supplementary.indicators.main_green
                                }
                              />
                              <Text
                                color={
                                  item["mae_improvement_%"] < 0
                                    ? "indicator.main_red"
                                    : "indicator.main_green"
                                }
                                fontWeight="bold"
                              >
                                {roundToTwoDecimalPlaces(
                                  item["mae_improvement_%"]
                                )}{" "}
                                %
                              </Text>
                            </HStack>
                          </HStack>
                          <Text
                            color="muted"
                            sx={{
                              "-webkit-box-orient": "vertical",
                              "-webkit-line-clamp": "2",
                              overflow: "hidden",
                              display: "-webkit-box",
                            }}
                          >
                            Trending{" "}
                            {item["mae_improvement_%"] == 0
                              ? "flat"
                              : item["mae_improvement_%"] > 0
                              ? "upwards"
                              : "downwards"}{" "}
                            for the next {report_stats["forecast_horizon"]}{" "}
                            Months. AI Backtests are{" "}
                            {roundToTwoDecimalPlaces(item["mae_improvement_%"])}
                            % better than benchmarks.
                          </Text>
                        </Stack>
                      )
                    )}
                </Stack>
              </Box>
              <VStack alignItems="left" width="100%">
                <Text fontWeight="bold" fontSize="2xl">
                  Feature Importance
                </Text>
                <Text>Features that influences the forecast of tourism:</Text>
                <Text>1. Consumer Confidence Index (UK)</Text>
                <Text>2. Gross Domestic Product (NZ)</Text>
                <Text>3. Gross Domestic Product (UK)</Text>
                <Text>4. Gross Domestic Product (India)</Text>
                <Text>5. Business Confidence Index (NZ)</Text>
                <Text>
                  The CCI (UK) is the leading feature in predicting the number
                  of tourists in Australia followed closely by GDP
                  (NZ/UK/India). This suggests that tourism in Australia may be
                  heavily influenced by economic factors in these regions.
                </Text>
                <Image
                  height="30rem"
                  width="30rem"
                  src="/reports/barplot.png"
                />
                <Text>
                  Features where low values have negative contribution to
                  tourism forecasting:
                </Text>
                <Text>1. CCI (UK)</Text>
                <Text>2. GDP (India)</Text>

                <Text>
                  Features where high values have positive contribution to
                  tourism forecasting:
                </Text>
                <Text>1. GDP (NZ)</Text>
                <Text>2. GDP (UK)</Text>
                <Text>3. BCI (NZ)</Text>
                <Text>
                  The high values (red) of CCI (UK) have a very high negative
                  contribution to the forecast of tourism while the low values
                  (green) have very high positive contribution. On the other
                  hand, the low values of GDP (NZ) have high negative
                  contribution while the high values have very high positive
                  contribution.{" "}
                </Text>
                <Image
                  height="30rem"
                  width="30rem"
                  src="/reports/beeswarm.png"
                />
              </VStack>
            </VStack>
          </HStack>
          <Accordion width="100%" allowToggle>
            <AccordionItem>
              <h2>
                <AccordionButton>
                  <Box as="span" flex="1" textAlign="left">
                    Backtest Result
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Stack spacing="3" width="full">
                  {backtestsTableData.data
                    .sort(
                      (
                        a: any, // eslint-disable-line @typescript-eslint/no-explicit-any
                        b: any // eslint-disable-line @typescript-eslint/no-explicit-any
                      ) =>
                        b[`${backtestType}${backtestSortBy}`] -
                        a[`${backtestType}${backtestSortBy}`]
                    )
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
                                          item[
                                            `${backtestType}_improvement_%`
                                          ] > 0
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
              </AccordionPanel>
            </AccordionItem>
          </Accordion>
        </VStack>
        {/* THIS IS THE NEWER VERSION OF REPORTS */}
      </VStack>
    );
  } else {
    return <></>;
  }
}
