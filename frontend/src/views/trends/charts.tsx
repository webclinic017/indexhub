import React, { useEffect, useRef } from "react";
import embed, { VisualizationSpec } from 'vega-embed';

interface VegaChartProps {
    spec: string;
    entityId: string;
    pointId?: number;
    cluster?: number;
}

export const VegaChart = (props: VegaChartProps) => {
    const { spec } = props;
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const runAsync = async () => {
            if (!containerRef.current || !spec) {
                return;
            }

            try {
                const result = await embed(
                    containerRef.current,
                    JSON.parse(spec) as VisualizationSpec,
                    { actions: false }
                );
                console.log(result.view);
            } catch (error) {
                console.error(error);
            }
        };

        runAsync();
    }, []);

    return <div ref={containerRef} style={{ height: "100%", width: "100%" }} />;
};

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
    // console.log(`getJsonVegaSpec response_json type=${typeof response_json} value=${JSON.stringify(response_json)}`);
    return response_json;
};
