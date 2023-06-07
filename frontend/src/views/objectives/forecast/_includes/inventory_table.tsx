import React, { useEffect, useState } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import Box from "@mui/material/Box";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import {
  HStack,
  Box as ChakraBox,
  VStack,
  Text,
  Stack,
  Spinner,
  Button,
} from "@chakra-ui/react";
import ReactEcharts from "echarts-for-react";
import { useAuth0AccessToken } from "../../../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../../../..";
import {
  getCombinedEntitiesAndInventoryTable,
  getEntitiesAndInventoryTables,
} from "../../../../utilities/backend_calls/tables";
import { getCombinedEntitiesAndInventoryChart } from "../../../../utilities/backend_calls/charts";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faNotebook } from "@fortawesome/pro-light-svg-icons";

const MuiTheme = createTheme({});

const entity_inventory_options_table_columns: GridColDef[] = [
  {
    field: "entity",
    headerName: "Entity",
    width: 300,
  },
];

const entity_inventory_table_columns: GridColDef[] = [
  {
    field: "time",
    headerName: "Time",
    width: 150,
    valueGetter: (params) => {
      if (!params.value) {
        return params.value;
      }
      return new Date(params.value).toLocaleDateString();
    },
  },
  {
    field: "inventory",
    headerName: "Inventory",
    width: 150,
  },
  {
    field: "actual",
    headerName: "Actual",
    width: 150,
  },
  {
    field: "baseline",
    headerName: "Baseline",
    width: 150,
  },
  {
    field: "ai",
    headerName: "AI",
    width: 150,
  },
  {
    field: "ai_10",
    headerName: "AI 10%",
    width: 150,
  },
  {
    field: "ai_90",
    headerName: "AI 90%",
    width: 150,
  },
  {
    field: "best_plan",
    headerName: "Best Plan",
    width: 150,
  },
  {
    field: "plan",
    headerName: "Plan",
    width: 150,
  },
];

export default function DataGridDemo(props: { objective_id: string }) {
  const [forecastAndInventoryEntities, setForecastAndInventoryEntities] =
    useState<Record<string, any> | null>(null);
  const [
    selectedForecastAndInventoryEntities,
    setSelectedForecastAndInventoryEntities,
  ] = useState<Record<string, string[] | string | null>>({
    forecast_entities: null,
    inventory_entity: null,
  });
  const [
    forecastAndInventoyEntitiesTableData,
    setForecastAndInventoyEntitiesTableData,
  ] = useState<Record<string, any>[] | null>(null);
  const [
    forecastAndInventoyEntitiesChartData,
    setForecastAndInventoyEntitiesChartData,
  ] = useState<Record<string, any> | null>(null);
  const [toggleGenerateInventoryData, setToggleGenerateInventoryData] =
    useState(false);
  const [isGeneratingInventoryData, setIsGeneratingInventoryData] =
    useState(false);
  const access_token_indexhub_api = useAuth0AccessToken();
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  useEffect(() => {
    const getEntitiesAndInventoryTablesApi = async () => {
      const entities = await getEntitiesAndInventoryTables(
        props.objective_id,
        access_token_indexhub_api
      );
      setForecastAndInventoryEntities(entities);
    };

    if (user_details.id && access_token_indexhub_api) {
      getEntitiesAndInventoryTablesApi();
    }
  }, [user_details, access_token_indexhub_api, props.objective_id]);

  useEffect(() => {
    const getInventoryDataApi = async () => {
      setIsGeneratingInventoryData(true);
      const forecast_inventory_table_data =
        await getCombinedEntitiesAndInventoryTable(
          props.objective_id,
          selectedForecastAndInventoryEntities,
          access_token_indexhub_api
        );
      setForecastAndInventoyEntitiesTableData(forecast_inventory_table_data);

      const forecast_inventory_chart_data =
        await getCombinedEntitiesAndInventoryChart(
          props.objective_id,
          selectedForecastAndInventoryEntities,
          access_token_indexhub_api
        );
      setForecastAndInventoyEntitiesChartData(forecast_inventory_chart_data);
      setIsGeneratingInventoryData(false);
    };

    if (toggleGenerateInventoryData) {
      getInventoryDataApi();
      setToggleGenerateInventoryData(false);
    }
  }, [toggleGenerateInventoryData]);

  return (
    <>
      {forecastAndInventoryEntities ? (
        <VStack
          width="100%"
          justify="space-between"
          mb="1rem"
          mt="1rem"
          alignItems="flex-start"
        >
          <VStack width="100%">
            <Text width="100%" fontSize="sm">
              Choose at least one entity and your preferred inventory to view
              the entity-inventory table below.
            </Text>
            <HStack width="100%">
              <ChakraBox width="50%">
                <Text fontWeight="bold">Entities</Text>
                <Text fontSize="sm">
                  Select entities to be included in the inventory data report.
                </Text>
                <Box sx={{ height: 400, width: "100%" }}>
                  <ThemeProvider theme={MuiTheme}>
                    <DataGrid
                      rows={forecastAndInventoryEntities["forecast_entities"]}
                      columns={entity_inventory_options_table_columns}
                      initialState={{
                        pagination: {
                          paginationModel: {
                            pageSize: 5,
                          },
                        },
                      }}
                      pageSizeOptions={[5]}
                      checkboxSelection
                      disableRowSelectionOnClick
                      onRowSelectionModelChange={(selectedEntityIds) => {
                        const selectedEntities: string[] = [];
                        selectedEntityIds.forEach((id) => {
                          selectedEntities.push(
                            forecastAndInventoryEntities["forecast_entities"][
                              id
                            ]["entity"]
                          );
                        });
                        selectedForecastAndInventoryEntities[
                          "forecast_entities"
                        ] = selectedEntities;
                        setSelectedForecastAndInventoryEntities(
                          structuredClone(selectedForecastAndInventoryEntities)
                        );
                      }}
                    />
                  </ThemeProvider>
                </Box>
              </ChakraBox>

              <ChakraBox width="50%">
                <Text fontWeight="bold">Inventories</Text>
                <Text fontSize="sm">
                  Select inventories to be included in the inventory data
                  report.
                </Text>
                <Box sx={{ height: 400, width: "100%" }}>
                  <ThemeProvider theme={MuiTheme}>
                    <DataGrid
                      rows={forecastAndInventoryEntities["inventory_entities"]}
                      columns={entity_inventory_options_table_columns}
                      initialState={{
                        pagination: {
                          paginationModel: {
                            pageSize: 5,
                          },
                        },
                      }}
                      pageSizeOptions={[5]}
                      onRowSelectionModelChange={(selectedEntityIds) => {
                        selectedForecastAndInventoryEntities[
                          "inventory_entity"
                        ] =
                          forecastAndInventoryEntities["inventory_entities"][
                            selectedEntityIds[0]
                          ]["entity"];
                        setSelectedForecastAndInventoryEntities(
                          structuredClone(selectedForecastAndInventoryEntities)
                        );
                      }}
                    />
                  </ThemeProvider>
                </Box>
              </ChakraBox>
            </HStack>
            <Button
              isDisabled={
                !(
                  selectedForecastAndInventoryEntities["forecast_entities"] &&
                  selectedForecastAndInventoryEntities["forecast_entities"]
                    .length > 0 &&
                  selectedForecastAndInventoryEntities["inventory_entity"]
                )
              }
              onClick={() => setToggleGenerateInventoryData(true)}
              mt="2rem !important"
              isLoading={isGeneratingInventoryData}
              loadingText={
                <>
                  <Text mr="0.5rem">Generating Inventory Data</Text>
                  <FontAwesomeIcon icon={faNotebook} />
                </>
              }
            >
              <Text mr="0.5rem">Generate Inventory Data</Text>
              <FontAwesomeIcon icon={faNotebook} />
            </Button>
          </VStack>

          <hr style={{ width: "100%", margin: "2rem 0" }}></hr>

          <VStack width="100%">
            {forecastAndInventoyEntitiesTableData &&
            forecastAndInventoyEntitiesChartData ? (
              <VStack width="100%" mt="unset !important">
                <ChakraBox width="100%">
                  <Text fontWeight="bold">Inventory Table</Text>
                  <Text fontSize="sm">
                    The table shows statistics for each entity and is sorted by
                    time (oldest to newest).
                  </Text>
                  <Box sx={{ height: 400, width: "100%" }}>
                    <ThemeProvider theme={MuiTheme}>
                      <DataGrid
                        rows={forecastAndInventoyEntitiesTableData}
                        columns={entity_inventory_table_columns}
                        initialState={{
                          pagination: {
                            paginationModel: {
                              pageSize: 5,
                            },
                          },
                        }}
                        pageSizeOptions={[5]}
                        disableRowSelectionOnClick
                      />
                    </ThemeProvider>
                  </Box>
                </ChakraBox>
                <ChakraBox width="100%" mt="2rem !important">
                  <Text fontWeight="bold">Inventory Chart</Text>
                  <Text fontSize="sm">
                    The lines represents the latest forecasts and panel trends
                    while the shaded area represents the quantile ranges.
                  </Text>
                  <ChakraBox height="25rem" py="1rem">
                    <ReactEcharts
                      option={forecastAndInventoyEntitiesChartData}
                      style={{
                        height: "100%",
                        width: "100%",
                      }}
                    />
                  </ChakraBox>
                </ChakraBox>
              </VStack>
            ) : (
              <Stack
                alignItems="center"
                borderRadius="10"
                justifyContent="center"
                height="full"
                backgroundColor="white"
                width="100%"
              >
                <Text>
                  Choose your preferred entities from the tables above and click
                  on &quot;Generate Inventory Data&quot;
                </Text>
              </Stack>
            )}
          </VStack>
        </VStack>
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
    </>
  );
}
