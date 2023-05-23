import React, { createContext, useState } from "react";
import Projector, { ProjectorData } from "./projector/projector";
import { HStack } from '@chakra-ui/react';
import TrendsSidebar from "./trends_sidebar";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";

export const TrendsContext = createContext({
    selectedPointIds: [] as number[],
    addPoint: (id: number) => { /* do nothing */ },
    removePoint: (id: number) => { /* do nothing */ },
    resetPoints: () => { /* do nothing */ },
    datasetId: "",
    setDatasetId: (datasetId: string) => { /* do nothing */ },
    apiToken: "",
    projectorData: {} as ProjectorData,
    updateProjectorData: (newData: ProjectorData) => { /* do nothing */ },
});


const MAX_CHARTS = 2;

export default function TrendsDashboard() {
    // Hold the shared state here
    const [selectedPointIds, setSelectedPointIds] = useState<number[]>([]);
    const [datasetId, setDatasetId] = useState<string>("commodities");
    const [projectorData, setProjectorData] = useState<ProjectorData>({} as ProjectorData);
    const apiToken = useAuth0AccessToken();


    const addPoint = (id: number) => {
        setSelectedPointIds((currIds) => {
            if (!currIds.includes(id) && currIds.length < MAX_CHARTS) {
                return [...currIds, id];
            }
            return currIds;
        });
    }

    const removePoint = (id: number) => {
        setSelectedPointIds((currIds) => currIds.filter(currId => currId !== id));
    }
    const resetPoints = () => {
        setSelectedPointIds([]);
    }

    const updateProjectorData = (newData: ProjectorData) => {
        setProjectorData(newData);
    }
    // Logging
    // useEffect(() => {
    //     console.log(`apiToken in trends: ${apiToken}`)
    // }, [apiToken]);

    // useEffect(() => {
    //     console.log(`selectedPoints in trends: ${selectedPoints.map(item => item.pointIndex as number)}`);
    // }, [selectedPoints]);
    return (
        <TrendsContext.Provider value={{
            selectedPointIds,
            addPoint,
            removePoint,
            resetPoints,
            datasetId,
            setDatasetId,
            apiToken,
            projectorData,
            updateProjectorData,
        }}>
            <HStack id="main_view" height="full" width="full" maxH='100%' >
                <Projector />
                <TrendsSidebar />
            </HStack>
        </TrendsContext.Provider>
    )
}