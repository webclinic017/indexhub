import React, { createContext, useEffect, useState } from "react";
import Projector, { ProjectorData } from "./projector/projector";
import { HStack } from '@chakra-ui/react';
import TrendsSidebar from "./trends_sidebar";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { useChatContext } from "./chat/chat_context";

export const TrendsContext = createContext({
    selectPoint: (_id: number) => { /* do nothing */ },
    selectedPointIds: [] as number[],
    addPoint: (_id: number) => { /* do nothing */ },
    removePoint: (_id: number) => { /* do nothing */ },
    resetPoints: () => { /* do nothing */ },
    datasetId: "",
    setDatasetId: (_datasetId: string) => { /* do nothing */ },
    apiToken: "",
    projectorData: {} as ProjectorData,
    updateProjectorData: (_newData: ProjectorData) => { /* do nothing */ },
});


const MAX_CHARTS = 2;

export default function TrendsDashboard() {
    // Hold the shared state here
    const [currentPointContext, setCurrentPointContext] = useState<number | null>(null);
    const [selectedPointIds, setSelectedPointIds] = useState<number[]>([]);
    const [datasetId, setDatasetId] = useState<string>("commodities");
    const [projectorData, setProjectorData] = useState<ProjectorData>({} as ProjectorData);
    const apiToken = useAuth0AccessToken();
    const { handleSendMessage } = useChatContext();


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
    const selectPoint = (id: number) => {
        console.log(`selectPoint: ${projectorData}`);
        setCurrentPointContext(id);
    }
    const resetPoints = () => {
        setSelectedPointIds([]);
    }

    const updateProjectorData = (newData: ProjectorData) => {
        setProjectorData(newData);
    }
    useEffect(() => {
        if (currentPointContext !== null) {
            console.log(`currentPointContext change: ${projectorData}`);
            const props = {
                "dataset_id": datasetId,
                "entity_id": projectorData.entityIds[currentPointContext],
            }
            console.log(`currentPointContext props: ${JSON.stringify(props)}`);
            handleSendMessage("load_context", props);
        }
    }, [currentPointContext]);
   
    return (
        <TrendsContext.Provider value={{
            selectPoint,
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