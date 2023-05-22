import React, { createContext, useEffect, useState } from "react";
import Projector from "./projector/projector";
import { HStack } from '@chakra-ui/react';
import { PointMetadata } from "scatter-gl";
import TrendsSidebar from "./trends_sidebar";

export const TrendsContext = createContext({
    selectedPoints: [] as PointMetadata[],
    addPoint: (point: PointMetadata) => { /* do nothing */ },
    removePoint: (pointIndex: number) => { /* do nothing */ }
});

export default function Trends() {
    // Hold the shared state here
    const [selectedPoints, setSelectedPoints] = useState<PointMetadata[]>([]);

    const addPoint = (point: PointMetadata) => {
        setSelectedPoints((prevPoints) => {
            const currPoints = prevPoints.map(item => item.pointIndex as number);
            if (!currPoints.includes(point.pointIndex as number)) {
                return [...prevPoints, point];
            }
            return prevPoints;
        });
    }

    const removePoint = (pointIndex: number) => {
        setSelectedPoints((prevPoints) => prevPoints.filter(prevPoint => prevPoint.pointIndex !== pointIndex));
    }

    useEffect(() => {
        console.log(`selectedPoints in trends: ${selectedPoints.map(item => item.pointIndex as number)}`);
    }, [selectedPoints]);
    return (
        <TrendsContext.Provider value={{ selectedPoints, addPoint, removePoint }}>
            <HStack id="main_view" height="full" width="full" maxH='100%' >
                <Projector />
                <TrendsSidebar />
            </HStack>
        </TrendsContext.Provider>
    )
}