import React, { useEffect, useState } from "react";
import {
  DataGridPremium,
  GridColDef,
  useGridApiRef,
  GridToolbar,
} from "@mui/x-data-grid-premium";
import { Box, Spinner, Stack, Text, VStack } from "@chakra-ui/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { useAuth0AccessToken } from "../../../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../../../..";
import { getForecastTableView } from "../../../../utilities/backend_calls/tables";

const MuiTheme = createTheme({});

export default function TableView(props: { objective_id: string }) {
  const [forecastTableData, setForecastTableData] = useState<Record<
    string,
    any
  > | null>(null);
  const [forecastTableGridCols, setForecastTableGridCols] = useState<
    GridColDef[]
  >([]);
  const access_token_indexhub_api = useAuth0AccessToken();
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  const apiRef = useGridApiRef();

  useEffect(() => {
    const getForecastDataApi = async () => {
      const forecast_table_data = await getForecastTableView(
        props.objective_id,
        access_token_indexhub_api
      );
      setForecastTableData(forecast_table_data);
      forecastTableGridCols.length = 0;
      forecast_table_data["columns"].forEach(
        (col_data: Record<string, any>) => {
          forecastTableGridCols.push({
            field: col_data["field"],
            headerName: col_data["headerName"].toUpperCase(),
            type: col_data["type"],
            width: ["forecast_10", "forecast_90"].includes(col_data["field"])
              ? 250
              : 200,
          } as GridColDef);
        }
      );
      forecastTableGridCols.push({
        field: "override",
        headerName: "OVERRIDE",
        type: "number",
        width: 200,
        editable: true,
      } as GridColDef);
      setForecastTableGridCols(structuredClone(forecastTableGridCols));
    };

    if (user_details.id && access_token_indexhub_api) {
      getForecastDataApi();
    }
  }, [user_details, access_token_indexhub_api, props.objective_id]);

  return (
    <Stack>
      {forecastTableData ? (
        <VStack
          width="100%"
          justify="space-between"
          mb="1rem"
          mt="1rem"
          alignItems="flex-start"
        >
          <VStack width="100%">
            <VStack width="100%" mt="unset !important">
              <Box width="100%">
                <Text fontWeight="bold">Forecast Table</Text>
                <Text fontSize="sm">
                  The table shows forecasts for each entity and is grouped by
                  entity(s).
                </Text>
                <Box height="45rem">
                  <ThemeProvider theme={MuiTheme}>
                    <DataGridPremium
                      rows={forecastTableData["rows"]}
                      apiRef={apiRef}
                      columns={forecastTableGridCols}
                      disableRowSelectionOnClick
                      initialState={{
                        aggregation: {
                          model: {
                            baseline: "sum",
                            forecast: "sum",
                            forecast_10: "sum",
                            forecast_90: "sum",
                            plan: "sum",
                            override: "sum",
                          },
                        },
                      }}
                      slots={{ toolbar: GridToolbar }}
                      // rowGroupingColumnMode="multiple"
                      rowGroupingModel={forecastTableData["group_by"]}
                    />
                  </ThemeProvider>
                </Box>
              </Box>
            </VStack>
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
