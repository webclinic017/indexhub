import React, { useEffect, useState } from "react";
import {
  DataGridPremium,
  GridColDef,
  useGridApiRef,
  GridRowParams,
} from "@mui/x-data-grid-premium";
import ReactEcharts from "echarts-for-react";
import {
  Box,
  Button,
  HStack,
  Spinner,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { useAuth0AccessToken } from "../../../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../../../..";
import {
  getCombinedEntitiesAndInventoryTable,
  getEntitiesAndInventoryTables,
} from "../../../../utilities/backend_calls/tables";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faNotebook } from "@fortawesome/pro-light-svg-icons";
import { getCombinedEntitiesAndInventoryChart } from "../../../../utilities/backend_calls/charts";

const MuiTheme = createTheme({});

export default function InventoryTable(props: { objective_id: string }) {
  const [forecastAndInventoryEntities, setForecastAndInventoryEntities] =
    useState<Record<string, any> | null>(null);
  const [
    forecastAndInventoryEntitiesGridCols,
    setForecastAndInventoryEntitiesGridCols,
  ] = useState<Record<string, GridColDef[]>>({ forecast: [], inventory: [] });
  const [
    selectedForecastAndInventoryEntities,
    setSelectedForecastAndInventoryEntities,
  ] = useState<Record<string, string[] | string | null>>({
    forecast_entities: null,
    inventory_entities: null,
  });
  const [
    forecastAndInventoyEntitiesTableData,
    setForecastAndInventoyEntitiesTableData,
  ] = useState<Record<string, any> | null>(null);
  const [
    forecastAndInventoryEntitiesTableGridCols,
    setForecastAndInventoryEntitiesTableGridCols,
  ] = useState<GridColDef[]>([]);
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

  const apiRef = useGridApiRef();

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
    if (forecastAndInventoryEntities) {
      ["forecast", "inventory"].forEach((table_type: string) => {
        forecastAndInventoryEntitiesGridCols[table_type] = [];
        forecastAndInventoryEntities[`${table_type}_entity_cols`].forEach(
          (col: string) => {
            forecastAndInventoryEntitiesGridCols[table_type].push({
              field: col,
              headerName: col.replaceAll("_", " ").toUpperCase(),
              width: 200,
            } as GridColDef);
            setForecastAndInventoryEntitiesGridCols(
              structuredClone(forecastAndInventoryEntitiesGridCols)
            );
          }
        );
      });
    }
  }, [forecastAndInventoryEntities]);

  useEffect(() => {
    const getInventoryDataApi = async () => {
      if (forecastAndInventoryEntities) {
        setIsGeneratingInventoryData(true);
        const forecast_inventory_table_data =
          await getCombinedEntitiesAndInventoryTable(
            props.objective_id,
            selectedForecastAndInventoryEntities,
            access_token_indexhub_api
          );
        setForecastAndInventoyEntitiesTableData(forecast_inventory_table_data);
        forecastAndInventoryEntitiesTableGridCols.length = 0;
        forecast_inventory_table_data["columns"].forEach(
          (col_data: Record<string, any>) => {
            forecastAndInventoryEntitiesTableGridCols.push({
              field: col_data["field"],
              headerName: col_data["headerName"].toUpperCase(),
              type: col_data["type"],
              width: 200,
            } as GridColDef);
            setForecastAndInventoryEntitiesTableGridCols(
              structuredClone(forecastAndInventoryEntitiesTableGridCols)
            );
          }
        );

        const forecast_inventory_chart_data =
          await getCombinedEntitiesAndInventoryChart(
            props.objective_id,
            selectedForecastAndInventoryEntities,
            access_token_indexhub_api
          );
        setForecastAndInventoyEntitiesChartData(forecast_inventory_chart_data);
        setIsGeneratingInventoryData(false);
      }
    };

    if (toggleGenerateInventoryData) {
      getInventoryDataApi();
      setToggleGenerateInventoryData(false);
    }
  }, [toggleGenerateInventoryData]);

  return (
    <Stack>
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
              <Box width="50%">
                <Text fontWeight="bold">Entities</Text>
                <Text fontSize="sm">
                  Select entities to be included in the inventory data report.
                </Text>
                <Box height="25rem">
                  <ThemeProvider theme={MuiTheme}>
                    <DataGridPremium
                      rows={forecastAndInventoryEntities["forecast_entities"]}
                      checkboxSelection
                      apiRef={apiRef}
                      columns={forecastAndInventoryEntitiesGridCols["forecast"]}
                      disableRowSelectionOnClick
                      isRowSelectable={(params: GridRowParams) =>
                        params.row.id > -1
                      }
                      rowGroupingColumnMode="multiple"
                      rowGroupingModel={forecastAndInventoryEntities[
                        "forecast_entity_cols"
                      ].slice(0, -1)}
                      onRowSelectionModelChange={(selectedEntityIds) => {
                        const selectedEntities: string[] = [];
                        selectedEntityIds.forEach((id) => {
                          const col_vals: string[] = [];
                          forecastAndInventoryEntities[
                            "forecast_entity_cols"
                          ].forEach((col: string) => {
                            col_vals.push(
                              forecastAndInventoryEntities["forecast_entities"][
                                id
                              ][col]
                            );
                          });
                          selectedEntities.push(col_vals.join(" - "));
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
              </Box>

              <Box width="50%">
                <Text fontWeight="bold">Inventories</Text>
                <Text fontSize="sm">
                  Select inventories to be included in the inventory data
                  report.
                </Text>
                <Box height="25rem">
                  <ThemeProvider theme={MuiTheme}>
                    <DataGridPremium
                      rows={forecastAndInventoryEntities["inventory_entities"]}
                      checkboxSelection
                      apiRef={apiRef}
                      columns={
                        forecastAndInventoryEntitiesGridCols["inventory"]
                      }
                      disableRowSelectionOnClick
                      isRowSelectable={(params: GridRowParams) =>
                        params.row.id > -1
                      }
                      rowGroupingColumnMode="multiple"
                      rowGroupingModel={forecastAndInventoryEntities[
                        "inventory_entity_cols"
                      ].slice(0, -1)}
                      onRowSelectionModelChange={(selectedEntityIds) => {
                        const selectedEntities: string[] = [];
                        selectedEntityIds.forEach((id) => {
                          const col_vals: string[] = [];
                          forecastAndInventoryEntities[
                            "inventory_entity_cols"
                          ].forEach((col: string) => {
                            col_vals.push(
                              forecastAndInventoryEntities[
                                "inventory_entities"
                              ][id][col]
                            );
                          });
                          selectedEntities.push(col_vals.join(" - "));
                        });
                        selectedForecastAndInventoryEntities[
                          "inventory_entities"
                        ] = selectedEntities;
                        setSelectedForecastAndInventoryEntities(
                          structuredClone(selectedForecastAndInventoryEntities)
                        );
                      }}
                    />
                  </ThemeProvider>
                </Box>
              </Box>
            </HStack>
            <Button
              isDisabled={
                !(
                  selectedForecastAndInventoryEntities["forecast_entities"] &&
                  selectedForecastAndInventoryEntities["forecast_entities"]
                    .length > 0 &&
                  selectedForecastAndInventoryEntities["inventory_entities"] &&
                  selectedForecastAndInventoryEntities["inventory_entities"]
                    .length > 0
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
                <Box width="100%">
                  <Text fontWeight="bold">Inventory Table</Text>
                  <Text fontSize="sm">
                    The table shows statistics for each entity and is sorted by
                    time (oldest to newest).
                  </Text>
                  <Box sx={{ height: 400, width: "100%" }}>
                    <ThemeProvider theme={MuiTheme}>
                      <DataGridPremium
                        rows={forecastAndInventoyEntitiesTableData["rows"]}
                        apiRef={apiRef}
                        columns={forecastAndInventoryEntitiesTableGridCols}
                        disableRowSelectionOnClick
                        // rowGroupingColumnMode="multiple"
                        rowGroupingModel={[
                          "time",
                          ...new Set([
                            ...forecastAndInventoryEntities[
                              "forecast_entity_cols"
                            ],
                            ...forecastAndInventoryEntities[
                              "inventory_entity_cols"
                            ],
                          ]),
                        ].slice(0, -1)}
                        initialState={{
                          aggregation: {
                            model: {
                              actual: "sum",
                              inventory: "avg",
                              baseline: "sum",
                              ai: "sum",
                              ai_10: "sum",
                              ai_90: "sum",
                              best_plan: "sum",
                              plan: "sum",
                            },
                          },
                        }}
                      />
                    </ThemeProvider>
                  </Box>
                </Box>
                <Box width="100%" mt="2rem !important">
                  <Text fontWeight="bold">Inventory Chart</Text>
                  <Text fontSize="sm">
                    The lines represents the latest forecasts and panel trends
                    while the shaded area represents the quantile ranges.
                  </Text>
                  <Box height="25rem" py="1rem">
                    <ReactEcharts
                      option={forecastAndInventoyEntitiesChartData}
                      style={{
                        height: "100%",
                        width: "100%",
                      }}
                    />
                  </Box>
                </Box>
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
    </Stack>
  );
}
