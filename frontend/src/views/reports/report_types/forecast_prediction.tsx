import React, { useState } from "react";
import { getChart, getTable } from "../../../utilities/backend_calls/report";
import {
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  VStack,
  HStack,
  Menu,
  MenuButton,
  MenuList,
  MenuItemOption,
  MenuOptionGroup,
} from "@chakra-ui/react"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import {faChevronDown} from "@fortawesome/free-solid-svg-icons";
import ReactEcharts from "echarts-for-react"
import { Report } from "../reports";

export type chartData = {
    chart_id: string,
    title: string,
    chart_type: string,
    readable_names: Record<string, never>,
    chart_data: Record<string, never>
  }

  export type forecastRecommendationsTable = {
    readable_names: Record<string, never>,
    time_series: {
      month_year: string[],
      rpt_forecast_10: number[],
      rpt_forecast_30: number[],
      rpt_forecast_50: number[],
      rpt_forecast_70: number[],
      rpt_forecast_90: number[]
    }
    title: string
  }

const initFilters = (report_filters: any) => {
    const filters_init: Record<string, any[]> = {}
        Object.keys(report_filters).forEach(key => {
            if (key == "quantile"){
                filters_init[key] = [0.1]
            } else {
                filters_init[key] = []
            }
        });
    return filters_init
}

export default function Forecast_Recommendations(props: {selectedReport: Report, access_token_indexhub_api: string, clearSelectedReport: () => void}) {

    const selectedReport = props.selectedReport
    const access_token_indexhub_api = props.access_token_indexhub_api
    const clearSelectedReport = props.clearSelectedReport
    const report_filters = selectedReport.filters

    const [chartData, setChartData] = useState<chartData>({chart_id: "", title : "", chart_type: "", readable_names: {}, chart_data: {}});
    const [tableData, setTableData] = useState<forecastRecommendationsTable>()
    const [filters, setFilters] = useState<Record<string, any[]>>(initFilters(report_filters))

    const getChartByChartId = async () => {
        const chart_response = await getChart(selectedReport?.chart_id, access_token_indexhub_api, filters)
        setChartData(chart_response)
    }

    const getTableByTableId = async () => {
        const table_response = await getTable(selectedReport?.table_id, access_token_indexhub_api, filters)
        setTableData(table_response.forecast_recommendations)
    }

    const updateFilter = (entity: string, value: any) => {
        const filters_temp = JSON.parse(JSON.stringify(filters))
        filters_temp[entity] = [].concat(value)
        setFilters(filters_temp)
    }

    React.useEffect(() => {
        if (access_token_indexhub_api && selectedReport.report_id){
            const filters_init: Record<string, any[]> = {}
            Object.keys(report_filters).forEach(key => {
                if (key == "quantile"){
                    filters_init[key] = [0.1]
                } else {
                    filters_init[key] = []
                }
            });
            setFilters(filters_init)

            getChartByChartId()
            getTableByTableId()
        }
    }, [selectedReport])

    React.useEffect(() => {
        getChartByChartId()
        getTableByTableId()
    }, [filters])

    const option = {
        title: {
          text: chartData.title
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: Object.values(chartData.readable_names)
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        toolbox: {
          feature: {
            saveAsImage: {}
          }
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: chartData.chart_data.time
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: chartData.readable_names.rpt_actual,
            type: chartData.chart_type,
            stack: chartData.readable_names.rpt_actual,
            data: chartData.chart_data.rpt_actual
          },
          {
            name: chartData.readable_names.rpt_manual,
            type: chartData.chart_type,
            stack: chartData.readable_names.rpt_manual,
            data: chartData.chart_data.rpt_manual
          },
          {
            name: chartData.readable_names.rpt_forecast,
            type: chartData.chart_type,
            stack: chartData.readable_names.rpt_forecast,
            data: chartData.chart_data.rpt_forecast
          },
        ]
      };

      return (
        <VStack padding="10px">
          <Button onClick={() => clearSelectedReport()} colorScheme="teal" size="sm">
              View all reports
          </Button>
          <VStack>
            <HStack width="100%" justifyContent="space-around">
            {Object.keys(report_filters).map((entity: string) => {
                return(
                    <VStack key={entity} width="30%" alignItems="flex-start">
                        <p>{report_filters[entity]["title"]}</p>
                        <Menu closeOnSelect={!report_filters[entity]["multiple_choice"]}>
                            <MenuButton as={Button} rightIcon={<FontAwesomeIcon icon={faChevronDown} />} width="100%">
                                {filters[entity].length == 0 ? "All" : filters[entity].length > 1 ? "Mutiple selections" : entity == "quantile" ? filters[entity][0] * 100 + "%" : filters[entity][0]}
                            </MenuButton>
                            <MenuList>
                                {report_filters[entity]["multiple_choice"] ?
                                    <MenuOptionGroup  type='checkbox' onChange={(value) =>{
                                        updateFilter(entity, value)
                                    }}>
                                        {report_filters[entity]["values"].map((item: any) => {
                                          return(
                                            <MenuItemOption  value={item} key={item}>{item}</MenuItemOption>
                                          )
                                        })}
                                    </MenuOptionGroup>
                                :
                                    report_filters[entity]["values"].map((item: any) => {
                                        return(
                                            <MenuItemOption  value={item} key={item} onClick={() => {updateFilter(entity, item)}}>{item}</MenuItemOption>
                                        )
                                    })
                                }
                            </MenuList>
                        </Menu>
                    </VStack>
                )
            })}
            </HStack>

            <ReactEcharts option={option} style={{
                    height: '35rem',
                    width: '90vw',
            }}/>

          </VStack>
          <VStack alignItems="flex-start" width="90vw">
            <p>{tableData?.title}</p>
            <TableContainer width="100%" backgroundColor="white" borderRadius="5px" title={tableData?.title}>
              <Table variant="striped">
                <Thead backgroundColor="#cbcbcb">
                  <Tr>
                    <Th>{tableData?.readable_names["month_year"]}</Th>
                    <Th>{tableData?.readable_names["trips_in_000s:indexhub_forecast_0.1"]}</Th>
                    <Th>{tableData?.readable_names["trips_in_000s:indexhub_forecast_0.3"]}</Th>
                    <Th>{tableData?.readable_names["trips_in_000s:indexhub_forecast_0.5"]}</Th>
                    <Th>{tableData?.readable_names["trips_in_000s:indexhub_forecast_0.7"]}</Th>
                    <Th>{tableData?.readable_names["trips_in_000s:indexhub_forecast_0.9"]}</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {Array(tableData?.time_series.month_year.length).fill(0).map((_, idx) => {
                    return (
                      <Tr key={idx}>
                        <Td>{tableData?.time_series.month_year[idx]}</Td>
                        <Td>{tableData?.time_series.rpt_forecast_10[idx]}</Td>
                        <Td>{tableData?.time_series.rpt_forecast_30[idx]}</Td>
                        <Td>{tableData?.time_series.rpt_forecast_50[idx]}</Td>
                        <Td>{tableData?.time_series.rpt_forecast_70[idx]}</Td>
                        <Td>{tableData?.time_series.rpt_forecast_90[idx]}</Td>
                      </Tr>
                    )
                  })}
                </Tbody>
              </Table>
            </TableContainer>
          </VStack>
        </VStack>
      )
}
