import React, { useContext, useEffect, useRef } from "react";
import { Stack, Text, ListItem, Button, Box, VStack, UnorderedList } from '@chakra-ui/react';
import { TrendsContext } from "./trends_dashboard";
import embed, { VisualizationSpec } from 'vega-embed';


export const getJsonVegaSpec = async (datasetId: string, entityId: string, apiToken: string) => {
    const charts_url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/trends/public/charts/${datasetId}/${entityId}`;
    const response = await fetch(
        charts_url,
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${apiToken}`,
            },
        }
    );
    const response_json = await response.json();
    console.log(`getJsonVegaSpec response_json type=${typeof response_json} value=${JSON.stringify(response_json)}`);
    return response_json;
};

const TrendsSidebarCharts = () => {
    const { selectedPointIds, removePoint, projectorData } = useContext(TrendsContext);

    return <Box id="trends-sidebar-charts" height="full" maxH='100%' maxW={'md'} boxShadow="xs" margin="5px">
        {selectedPointIds.length <= 0 ? (<Text fontSize={{ base: 'sm' }} color={'gray.500'}>
            Each point is a time series embedding.
            Click on a point to add it to the list below.
            Hold left click to rotate the view.
            Hold right click to pan around.
            Scroll to zoom in and out.
            Select up to 2 points to compare.
        </Text>) : (
            <UnorderedList>
                {selectedPointIds.map((pointId) => {
                    const entityId = projectorData.entityIds[pointId];
                    const cluster = projectorData.clusters[pointId];

                    return (
                        <ListItem key={pointId} margin={"5px"} listStyleType='none'>
                            <VStack height={"100%"} width={"100%"}>
                                {/* <VegaChart entityId={entityId} cluster={cluster} /> */}
                                <Stack direction='row' spacing={4} align='center' margin={"5px"}>
                                    <Text fontSize={{ base: 'sm' }} color={'gray.500'}>
                                        pointId={pointId} entityId={entityId} cluster={cluster}
                                    </Text>
                                    <Button size='xs' colorScheme='red'  onClick={() => {
                                        removePoint(pointId);
                                    }}>
                                        Remove
                                    </Button>
                                </Stack>
                            </VStack>
                        </ListItem>
                    )
                })}
            </UnorderedList>)}
    </Box>;
}

interface VegaChartProps {
    pointId?: number;
    entityId: string;
    cluster?: number;
    spec: string;
}

export const VegaChart = (props: VegaChartProps) => {
    const { spec } = props;
    const containerRef = useRef<HTMLDivElement>(null);
    // const { datasetId, apiToken } = useContext(TrendsContext);

    useEffect(() => {
        const runAsync = async () => {
            if (!containerRef.current) return;
            try {
                const result = await embed(containerRef.current, JSON.parse(spec) as VisualizationSpec);
                console.log(result.view);
            } catch (error) {
                console.error(error);
            }
        };

        runAsync();
    }, []); // The empty array as second argument to useEffect makes it run only once

    return <div ref={containerRef} style={{ height: "100%", width: "100%" }} />;
};

export default TrendsSidebarCharts;