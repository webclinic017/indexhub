import { Card, CardBody } from "@chakra-ui/card";
import {
  Box,
  Button,
  Container,
  Flex,
  Grid,
  Heading,
  HStack,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { faArrowsToCircle, faChartLine, faCircleDot, faDatabase, faPlusCircle } from "@fortawesome/pro-light-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import { ReadyState } from "react-use-websocket";
import { useWebSocket } from "react-use-websocket/dist/lib/use-websocket";
import { AppState } from "../..";
import { colors } from "../../theme/theme";
import { capitalizeFirstLetter } from "../../utilities/helpers";

export type Objective = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const objective_status_to_color: any = {
  RUNNING: colors.supplementary.diverging_color.main_yellow,
  COMPLETED: colors.supplementary.indicators.main_green,
  SUCCESS: colors.supplementary.indicators.main_green,
  FAILED: colors.supplementary.indicators.main_red,
};

const ObjectivesDashboard = () => {
  const { sendMessage, lastMessage, readyState } = useWebSocket(
    `${process.env.REACT_APP__FASTAPI__WEBSOCKET_DOMAIN}/objectives/ws`
  );
  const [objectives, setObjectives] = useState<Objective[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [wsCallStarted, setWsCallStarted] = useState(false);
  const navigate = useNavigate();
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  const getObjectivesByUserId = () => {
    sendMessage(JSON.stringify({ user_id: user_details.id }));
  };

  useEffect(() => {
    if (user_details.id && readyState == ReadyState.OPEN && !wsCallStarted) {
      getObjectivesByUserId();
      setWsCallStarted(true);
    }
  }, [user_details, readyState, wsCallStarted]);

  useEffect(() => {
    if (lastMessage?.data) {
      const objectives: Record<"objectives", Objective[]> = JSON.parse(
        lastMessage.data
      );
      objectives["objectives"].map((objective: Objective) => {
        objective["fields"] = JSON.parse(objective["fields"]);
      });
      setObjectives(objectives["objectives"]);

      if (Object.keys(JSON.parse(lastMessage.data)).includes("objectives")) {
        const statuses: string[] = [];
        const objectives: Objective[] = JSON.parse(lastMessage.data).objectives;
        objectives.forEach((objective) => {
          statuses.push(objective.status);
        });
        if (statuses.includes("RUNNING")) {
          setTimeout(getObjectivesByUserId, 5000);
        }
      }
    }
  }, [lastMessage]);

  return (
    <VStack width="100%" spacing="8">
      <Text fontSize="2xl" fontWeight="bold" width="100%" textAlign="left">
        Your Objectives
      </Text>
      <HStack width="100%" justify="space-between">
        <Card p="1rem" width="49%" cursor="pointer" onClick={() => navigate("/objectives/new_objective")}>
          <HStack height="100%">
            <VStack height="100%" alignItems="flex-start" justify="space-between">
              <VStack mb="6" alignItems="flex-start">
                <Flex p="1rem" mb="2" border="1px solid #eeeef1" borderRadius="8">
                  <FontAwesomeIcon icon={faChartLine as any} />
                </Flex>
                <Heading fontSize="md">New Objective</Heading>
                <Text color="text.gray">Create new objectives from your sources</Text>
              </VStack>
              <Button>Create new</Button>
            </VStack>
          </HStack>
        </Card>
      </HStack>
      <hr style={{ width: "100%", margin: "3rem 0" }}></hr>
      {objectives.length > 0 ? (
        <>
          <Grid templateColumns="repeat(3, 1fr)" gap={6} mt="unset !important">
            {objectives.map((objective, idx) => {
              return (
                <Card
                  cursor="pointer"
                  boxShadow="md"
                  borderRadius="lg"
                  key={idx}
                  bgColor="white"
                  onClick={() => {
                    navigate(`forecast/${objective["id"]}`)
                  }}
                >
                  <CardBody>
                    <VStack p="4">
                      <HStack width="100%" justify="left">
                        <Text
                          pr={2}
                          fontSize="2xs"
                          textTransform="uppercase"
                          fontWeight="bold"
                        >
                          {objective["tag"]}
                        </Text>
                        <Text
                          pl={2}
                          fontSize="2xs"
                          borderLeft="1px solid"
                          margin="unset !important"
                        >
                          {new Date(objective["created_at"]).toLocaleDateString()}
                        </Text>
                      </HStack>

                      <Text width="100%" textAlign="left" fontWeight="bold">
                        {capitalizeFirstLetter(objective["name"])}
                      </Text>

                      <HStack width="100%" justify="space-between">
                        <HStack>
                          <FontAwesomeIcon
                            size="2xs"
                            icon={faCircleDot as any}
                            beatFade
                            style={{
                              color: objective_status_to_color[objective["status"]],
                            }}
                          />
                          <Text
                            textAlign="center"
                            fontSize="2xs"
                            color={objective_status_to_color[objective["status"]]}
                            pl="1"
                          >
                            {objective["status"]}
                          </Text>
                        </HStack>

                        <Text
                          textAlign="center"
                          fontSize="2xs"
                          textTransform="uppercase"
                        >
                          Last Updated :{" "}
                          {new Date(objective["updated_at"]).toLocaleString()}
                        </Text>
                      </HStack>

                      <Text py={6} textAlign="left" fontWeight="bold">
                        {capitalizeFirstLetter(objective["fields"]["description"])}
                      </Text>

                      <VStack width="100%" justify="left">
                        <Text width="100%" fontSize="xs">
                          SOURCES
                        </Text>
                        <Text width="100%" fontSize="small">
                          <b>PANEL:</b> Panel Source Name
                        </Text>
                        <Text width="100%" fontSize="small">
                          <b>BASELINE:</b> Baseline Source Name
                        </Text>
                      </VStack>

                      {/* <Box p="6">{logos[source_type]}</Box> */}
                    </VStack>
                  </CardBody>
                </Card>
              );
            })}
            <Card
              cursor="pointer"
              borderRadius="lg"
              alignItems="center"
              justifyContent="center"
              onClick={() => {
                navigate("/objectives/new_objective");
              }}
            >
              <CardBody>
                <VStack>
                  <FontAwesomeIcon size="2x" icon={faPlusCircle as any} />
                  <Text>Add a new objective</Text>
                </VStack>
              </CardBody>
            </Card>
          </Grid>
        </>
      ) : <></>}
    </VStack>
  );
};

export default ObjectivesDashboard;
