import React, { createContext, useContext, useEffect, useState } from "react";
import { ProjectorData } from "./projector";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { useChatContext } from "../chat/chat_context";
import { TrendsListItemProps } from "./trends_landing";

export const useTrendsContext = () => useContext(TrendsContext);

export const TrendsContext = createContext({
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  selectPoint: (_id: number) => {
    /* do nothing */
  },
  selectedPointIds: [] as number[],
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  addPoint: (_id: number) => {
    /* do nothing */
  },
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  removePoint: (_id: number) => {
    /* do nothing */
  },
  resetPoints: () => {
    /* do nothing */
  },
  datasetId: "",
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setDatasetId: (_datasetId: string) => {
    /* do nothing */
  },
  apiToken: "",
  projectorData: null as ProjectorData | null,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  updateProjectorData: (_newData: ProjectorData) => {
    /* do nothing */
  },
  trendsList: [] as TrendsListItemProps[],
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setTrendsList: (_trendsList: TrendsListItemProps[]) => {
    /* do nothing */
  },
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setCurrentEntityId: (_entityId: string) => {
    /* do nothing */
  },
});

const MAX_CHARTS = 2;

const TrendsContextProvider = (props: { children: React.ReactNode }) => {
  // Hold the shared state here
  const [currentEntityId, setCurrentEntityId] = useState<string | null>(null);
  const [currentPointContext, setCurrentPointContext] = useState<number | null>(
    null
  );
  const [selectedPointIds, setSelectedPointIds] = useState<number[]>([]);
  const [datasetId, setDatasetId] = useState<string>("commodities");
  const [projectorData, setProjectorData] = useState<ProjectorData | null>(
    null
  );
  const [trendsList, setTrendsList] = useState<TrendsListItemProps[]>([]);
  const apiToken = useAuth0AccessToken();
  const { handleSendMessage, onOpenChatBot } = useChatContext();

  const addPoint = (id: number) => {
    setSelectedPointIds((currIds) => {
      if (!currIds.includes(id) && currIds.length < MAX_CHARTS) {
        return [...currIds, id];
      }
      return currIds;
    });
  };

  const removePoint = (id: number) => {
    setSelectedPointIds((currIds) => currIds.filter((currId) => currId !== id));
  };
  const selectPoint = (id: number) => {
    console.log(`selectPoint: ${projectorData}`);
    setCurrentPointContext(id);
  };
  const resetPoints = () => {
    setSelectedPointIds([]);
  };

  const updateProjectorData = (newData: ProjectorData) => {
    setProjectorData(newData);
  };

  useEffect(() => {
    console.log(`currentEntityId change: ${currentEntityId}`);
    if (!currentEntityId || !datasetId) {
      return;
    }
    const props = {
      dataset_id: datasetId,
      entity_id: currentEntityId,
    };
    handleSendMessage("load_context", props);
    onOpenChatBot();
    console.log(`currentEntityId change done: ${currentEntityId}`);
  }, [currentEntityId]);

  useEffect(() => {
    console.log(`currentPointContext change: ${currentEntityId}`);

    if (!currentPointContext || !projectorData) {
      return;
    }
    setCurrentEntityId(projectorData.entityIds[currentPointContext]);
    console.log(`currentPointContext change done: ${currentEntityId}`);
  }, [currentPointContext]);

  return (
    <TrendsContext.Provider
      value={{
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
        trendsList,
        setTrendsList,
        setCurrentEntityId,
      }}
    >
      {props.children}
    </TrendsContext.Provider>
  );
};

export default TrendsContextProvider;
