import { Box, Button, FormControl, FormLabel, HStack, Heading, IconButton, Input, Modal, ModalBody, ModalCloseButton, ModalContent, ModalHeader, ModalOverlay, Spinner, Stack, StackDivider, TableContainer, Text, VStack, useDisclosure } from "@chakra-ui/react"
import { Select } from "chakra-react-select"
import React, { useEffect, useState } from "react"
import { useAuth0AccessToken } from "../../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../../..";
import { getPolicy } from "../../../utilities/backend_calls/policy";
import { Policy } from "../policies_dashboard";
import { useParams } from "react-router-dom";
import { createColumnHelper } from "@tanstack/react-table";
import { DataTable } from "../../../components/table";
import { Stat } from "../../../components/stats";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPenToSquare } from "@fortawesome/free-regular-svg-icons";
import { getTrendChart } from "../../../utilities/backend_calls/charts";
import ReactEcharts from "echarts-for-react";

const ai_recommendation_table_json = {
  "table_data": {
    "Adelaide": [
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 1,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 2,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 3,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
    ],
    "Brisbane & Gold Coast": [
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 1,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 2,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 3,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
    ],
    "Canberra": [
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 1,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 2,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
      {
        "date": '2019-03-01T00:00:00',
        "forecast_horizon": 3,
        "benchmark": 100,
        "ai_forecast": 101,
        "ai_forecast_90": 90,
        "ai_forecast_10": 110,
        "override": null
      },
    ],
  },
  "sum_ai_forecasts": 909,
  "sum_actual": 506,
  "readable_names": {
    "date": "Date",
    "forecast_horizon": "Forecast Horizon",
    "benchmark": "Benchmark",
    "ai_forecast": "AI Forecast",
    "ai_forecast_90": "90% Forecast",
    "ai_forecast_10": "10% Forecast",
    "override": "Override"
  }
}

const dummy_stats = [
  { label: 'Total Subscribers', value: '71,887', delta: { value: '321', isUpwardsTrend: true } },
  { label: 'Avg. Open Rate', value: '56.87%', delta: { value: '2.3%', isUpwardsTrend: true } },
  { label: 'Avg. Click Rate', value: '12.87%', delta: { value: '0.1%', isUpwardsTrend: false } },
]

const dummy_data = [
  {
    entity: "019340",
    volatility: "0.31",
    forecast_10: "268",
    forecast_50: "504",
    forecast_90: "698",
    baseline: "750",
    ai: "583",
    manual_override: "",
  },
  {
    entity: "019341",
    volatility: "0.31",
    forecast_10: "268",
    forecast_50: "504",
    forecast_90: "698",
    baseline: "750",
    ai: "583",
    manual_override: "",
  },
  {
    entity: "019342",
    volatility: "0.31",
    forecast_10: "268",
    forecast_50: "504",
    forecast_90: "698",
    baseline: "750",
    ai: "583",
    manual_override: "",
  },
  {
    entity: "019343",
    volatility: "0.31",
    forecast_10: "268",
    forecast_50: "504",
    forecast_90: "698",
    baseline: "750",
    ai: "583",
    manual_override: "",
  },
]

type AI_Recommendation_Table = Record<string, any>

const PolicyForecast = () => {
  const { policy_id } = useParams()
  const [policy, setPolicy] = useState<Policy | null>(null)

  const [mainTrendChart, setMainTrendChart] = useState<Record<any, any> | null>(null)

  const access_token_indexhub_api = useAuth0AccessToken();
  const user_details = useSelector((state: AppState) => state.reducer?.user);
  const [AIRecommendationTable, setAIRecommendationTable] = useState<AI_Recommendation_Table[]>(dummy_data)
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

  const AI_Recommendation_column_helper = createColumnHelper<AI_Recommendation_Table>();

  const manualOverrideAi = (manual_forecast = "", entity: string) => {
    console.log(manualOverrideVal)
    console.log(manualOverrideEntity)

    const upd_obj_index = AIRecommendationTable.findIndex(((obj: any) => obj["entity"] == entity));
    AIRecommendationTable[upd_obj_index]["manual_override"] = manual_forecast
    console.log(AIRecommendationTable)
    setAIRecommendationTable([...AIRecommendationTable])


    setManualOverrideEntity("")
    setManualOverrideVal("")
    onCloseManualOverrideModal()
  }

  const columns = [
    AI_Recommendation_column_helper.accessor("entity", {
      cell: (info) => (
        <VStack onClick={() => { onOpenTrendModal() }} alignItems="flex-start">
          <Text>
            {info.getValue()}
          </Text>
        </VStack>
      ),
      header: "Entities",
    }),
    AI_Recommendation_column_helper.accessor("volatility", {
      cell: (info) => (
        <VStack onClick={() => { onOpenTrendModal() }} alignItems="flex-start">
          <Text>
            {info.getValue()}
          </Text>
        </VStack>
      ),
      header: "Volatility",
    }),
    AI_Recommendation_column_helper.accessor("forecast_10", {
      cell: (info) => (
        <VStack onClick={() => { onOpenTrendModal() }} alignItems="flex-start">
          <Text>
            {info.getValue()}
          </Text>
        </VStack>
      ),
      header: "Forecast (10%)",
    }),
    AI_Recommendation_column_helper.accessor("forecast_50", {
      cell: (info) => (
        <VStack onClick={() => { onOpenTrendModal() }} alignItems="flex-start">
          <Text>
            {info.getValue()}
          </Text>
        </VStack>
      ),
      header: "Forecast (50%)",
    }),
    AI_Recommendation_column_helper.accessor("forecast_90", {
      cell: (info) => (
        <VStack onClick={() => { onOpenTrendModal() }} alignItems="flex-start">
          <Text>
            {info.getValue()}
          </Text>
        </VStack>
      ),
      header: "Forecast (90%)",
    }),
    AI_Recommendation_column_helper.accessor("baseline", {
      cell: (info) => (
        <VStack onClick={() => { onOpenTrendModal() }} alignItems="flex-start">
          <Text>
            {info.getValue()}
          </Text>
        </VStack>
      ),
      header: "Baseline Forecast",
    }),
    AI_Recommendation_column_helper.accessor("ai", {
      cell: (info) => (
        <VStack onClick={() => { onOpenTrendModal() }} alignItems="flex-start">
          <Text>
            {info.getValue()}
          </Text>
        </VStack>
      ),
      header: "AI Forecast",
    }),

    AI_Recommendation_column_helper.accessor(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (row: any) => [
        row["entity"],
        row["manual_override"],
      ],
      {
        id: "manual_override",
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
        header: "Manual Override",
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
    if (access_token_indexhub_api && user_details.id) {
      getPolicyApi();
      getMainTrendChartApi()
    }
  }, [access_token_indexhub_api, user_details]);


  useEffect(() => {
    console.log(policy)
  }, [policy])

  useEffect(() => {
    console.log(mainTrendChart)
  }, [mainTrendChart])

  if (policy) {
    return (
      <>
        <VStack width="100%" alignItems="flex-start">

          <Heading>AI Forecast</Heading>

          {/* Policy Description */}
          <Text mb="1.5rem !important">{policy["fields"]["description"]}</Text>

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

          {/* Stats */}
          <Box my="1.5rem !important" width="100%">
            <Stack direction="row" divider={<StackDivider />} spacing="0">
              {dummy_stats.map((stat, id) => (
                <Stat key={id} flex="1" {...stat} />
              ))}
            </Stack>
          </Box>

          {/* Top AI Recommendations */}
          <Box my="1.5rem !important" width="100%">
            <HStack mb="1rem" justify="space-between" pr="1rem">
              <Text fontWeight="bold">Top AI Recommendations Table</Text>
              <Button>Export</Button>
            </HStack>
            <TableContainer width="100%" backgroundColor="white">
              <DataTable
                columns={columns}
                data={AIRecommendationTable}
                body_height="73px"
              ></DataTable>
            </TableContainer>
          </Box>

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