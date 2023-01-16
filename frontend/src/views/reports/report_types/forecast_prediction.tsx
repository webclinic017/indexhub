import React, { useState } from "react";
import { getChart, getTable } from "../../../utilities/backend_calls/report";
import {
  Table,
  Thead,
  Tbody,
  Tr,
  Td,
  TableContainer,
  VStack,
  HStack,
  Text,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SliderMark,
  Container
} from "@chakra-ui/react"
import { createColumnHelper } from "@tanstack/react-table";
import { DataTable } from "../../../components/data_table"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck
} from "@fortawesome/free-solid-svg-icons";

import ReactEcharts from "echarts-for-react"
import { Report } from "../reports";

export type chartData = {
    chart_id: string,
    title: string,
    chart_type: string,
    readable_names: Record<string, never>,
    chart_data: Record<string, never>
  }

type Forecast_Recommendations_Table = {
  month_year: string;
  rpt_forecast_10: string;
  rpt_forecast_30: string;
  rpt_forecast_50: string;
  rpt_forecast_70: string;
  rpt_forecast_90: string;
};

export type forecastRecommendationsTable = {
  readable_names: Record<string, never>,
  data: Forecast_Recommendations_Table[],
  title: string
}

const initFilters = (report_filters: any) => {
    const filters_init: Record<string, any[]> = {}
        Object.keys(report_filters).forEach(key => {
          filters_init[key] = []
        });
    filters_init["quantile"] = [0.1]
    return filters_init
}

export default function Forecast_Recommendations(props: {selectedReport: Report, access_token_indexhub_api: string, clearSelectedReport: () => void}) {

    const selectedReport = props.selectedReport
    const access_token_indexhub_api = props.access_token_indexhub_api
    const report_filters = selectedReport.entities["forecast_recommendations"]

    const [chartData, setChartData] = useState<chartData>({chart_id: "", title : "", chart_type: "", readable_names: {}, chart_data: {}});
    const [tableData, setTableData] = useState<forecastRecommendationsTable>({readable_names: {}, data:[{month_year: "", rpt_forecast_10: "", rpt_forecast_30: "", rpt_forecast_50: "", rpt_forecast_70: "", rpt_forecast_90: ""}], title: ""})
    const [filters, setFilters] = useState<Record<string, any[]>>(initFilters(report_filters))

    const sliderLabelStyles = {
      mt: '2',
      ml: '-2.5',
      fontSize: 'sm',
    }

    const getChartByChartId = async () => {
        const chart_response = await getChart(selectedReport?.chart_id, access_token_indexhub_api, filters)
        setChartData(chart_response)
    }

    const getTableByTableId = async () => {
        const table_response = await getTable(selectedReport?.table_id, access_token_indexhub_api, filters)
        setTableData(table_response.forecast_recommendations)
    }

    const updateFilter = (entity: string, value: any, is_multiple = true) => {
        let choices = filters[entity]
        const filters_internal = JSON.parse(JSON.stringify(filters))

        if (is_multiple){
          const index = choices.indexOf(value);
          if (index > -1) { // only splice array when item is found
            choices.splice(index, 1); // 2nd parameter means remove one item only
          } else {
            choices.push(value)
          }
        } else {
          choices = [value]
        }
        filters_internal[entity] = choices
        setFilters(filters_internal)
    }

    React.useEffect(() => {
        if (access_token_indexhub_api && selectedReport.report_id){
            const filters_init: Record<string, any[]> = {}
            Object.keys(report_filters).forEach(key => {
              filters_init[key] = []
            });
            filters_init["quantile"] = [0.1]
            setFilters(filters_init)

            getChartByChartId()
            getTableByTableId()
        }
    }, [selectedReport])

    React.useEffect(() => {
        getChartByChartId()
        getTableByTableId()
    }, [filters])



    const table_data = tableData?.data

    const columnHelper = createColumnHelper<Forecast_Recommendations_Table>();

    const columns = [
      columnHelper.accessor("month_year", {
        cell: (info) => info.getValue(),
        header: "Month"
      }),
      columnHelper.accessor("rpt_forecast_10", {
        cell: (info) => info.getValue(),
        header: "AI Forecast (10%)"
      }),
      columnHelper.accessor("rpt_forecast_30", {
        cell: (info) => info.getValue(),
        header: "AI Forecast (30%)"
      }),
      columnHelper.accessor("rpt_forecast_50", {
        cell: (info) => info.getValue(),
        header: "AI Forecast (50%)"
      }),
      columnHelper.accessor("rpt_forecast_70", {
        cell: (info) => info.getValue(),
        header: "AI Forecast (70%)"
      }),
      columnHelper.accessor("rpt_forecast_90", {
        cell: (info) => info.getValue(),
        header: "AI Forecast (90%)"
      }),
    ];

    const option = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: Object.values(chartData.readable_names),
          left: "2%"
        },
        grid: {
          left: '0',
          right: '0',
          bottom: '3%',
          containLabel: true
        },
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
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
        dataZoom: [
          {
            type: 'inside',
            start: 0
          },
          {
            start: 0
          }
        ],
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
          <Text width="90vw" textAlign="left" fontSize="2xl" fontWeight="bold">Forecast Recommendations</Text>
          <VStack>
            <VStack width="90vw" alignItems="flex-start" padding="4rem 0">
              <HStack width="100%" justifyContent="flex-start" overflowX="scroll">
              {Object.keys(report_filters).map((entity, idx) => {
              return(
                <VStack key={idx} width="100%" maxWidth="35rem" minWidth="25rem" height="15rem" alignItems="flex-start" border="1px solid #ecf0f3" padding="1rem">
                  <Text lineHeight="0.5" fontSize="sm" fontWeight="bold">All {entity}s</Text>
                  <Text width="100%" paddingBottom="0.5rem" borderBottom="1px solid #c6c9cc"  fontSize="xs">Choose your preferred {entity}s you would like to filter with (multiple choices)</Text>
                  <TableContainer width="100%" backgroundColor="white" overflowY="scroll">
                    <Table>
                      <Thead backgroundColor="#f7fafc">
                      </Thead>
                      <Tbody>
                          {report_filters[entity]["values"].map((value: string, idx: number) => {
                            return (
                              <Tr cursor="pointer" key={idx} onClick={() => {updateFilter(entity, value)}}>
                                <Td padding="unset" height="33px" fontSize="sm" >{idx + 1}</Td>
                                <Td padding="unset" height="33px" fontSize="sm" textAlign="center" >{value}</Td>
                                {filters[entity].includes(value) ?
                                <Td height="33px" padding="unset"><FontAwesomeIcon icon={faCheck}/></Td>
                                :
                                <Td></Td>}
                              </Tr>
                            )
                          })}
                      </Tbody>
                    </Table>
                  </TableContainer>
                </VStack>
              )})}
              </HStack>
              <VStack marginTop="4.5rem !important" width="100%" maxWidth="35rem" alignItems="flex-start" paddingInline="20px" padding="unset">
                <Text textAlign="left" fontSize="lg" fontWeight="bold">AI Forecast Adjustment:</Text>
                <Text textAlign="left" fontSize="sm" >Subtitle for the quantile slider here</Text>
                <Container marginTop="3rem !important" justifyContent="center" alignItems="center" display="flex" height="100%" flexDirection="column" maxWidth="unset">
                  <Slider defaultValue={0.1} min={0.1} max={0.9} step={0.05} aria-label='slider-ex-6' onChange={(val) => updateFilter("quantile", val, false)}>
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
                      textAlign='center'
                      color={filters["quantile"][0] < 0.5 ? "#9E2B2B" : "#44AA7E"}
                      mt='-10'
                      ml='-5'
                      w='12'
                    >
                      {Math.floor(((filters["quantile"][0] - 0.5) / 0.4) * 100)}%
                    </SliderMark>
                    <SliderTrack backgroundColor="#44AA7E">
                      <SliderFilledTrack backgroundColor="#9E2B2B"/>
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                </Container>
              </VStack>
            </VStack>

            <Text width="90vw" textAlign="left" fontSize="xl" fontWeight="bold">Title for Chart</Text>
            <Text width="90vw" textAlign="left" fontSize="sm" >Placeholder for a more descriptive subtitle for the chart here</Text>
            <ReactEcharts option={option} style={{
                    height: '35rem',
                    width: '100%',
                    margin: "2rem 0"
            }}/>

          </VStack>
          <VStack alignItems="flex-start" width="90vw">
            <Text width="95%" textAlign="left" fontSize="xl" fontWeight="bold">Title for Table</Text>
            <Text width="95%" textAlign="left" fontSize="sm"  marginBottom="1rem !important">Placeholder for a more descriptive subtitle for the table here</Text>
            <DataTable columns={columns} data={table_data} />
          </VStack>
        </VStack>
      )
}
