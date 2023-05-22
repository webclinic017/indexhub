import React, { useEffect, useState } from "react";
import {
  Text,
  VStack,
  Stack,
  Button,
  Flex,
  HStack,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalCloseButton,
  ModalBody,
  useDisclosure,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Grid,
  useToast,
  Spinner,
  Heading
} from "@chakra-ui/react";
import { useSelector } from "react-redux";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { AppState } from "../../index";
import { Card } from "@chakra-ui/card";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ReactComponent as S3Logo } from "../../assets/images/svg/s3.svg";
import { ReactComponent as AzureLogo } from "../../assets/images/svg/azure.svg";
import { faCircleDot } from "@fortawesome/pro-light-svg-icons";
import { colors } from "../../theme/theme";
import { faArrowsToCircle, faDatabase } from "@fortawesome/pro-light-svg-icons";
import NewSource from "./new_source";
import NewIntegration from "./new_integration";
import { getUserIntegrations } from "../../utilities/backend_calls/integration";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { setUserIntegrations as setUserIntegrationsApi } from "../../utilities/backend_calls/integration";
import Toast from "../../components/toast";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const logos: Record<string, any> = {
  s3: <S3Logo width="100%" />,
  azure: <AzureLogo width="100%" />,
};

const status_colors: Record<string, any> = {
  SUCCESS: colors.supplementary.indicators.main_green,
  RUNNING: colors.supplementary.diverging_color.main_yellow,
  FAILED: colors.supplementary.indicators.main_red,
};

export type Source = {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  datetime_fmt: string;
  columns: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  freq: string;
  output_path: string;
  status: string;
  tag: string;
  variables: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  fields: Record<string, any>
  msg: string;
  target_cols: string; // to be removed when refactoring objectives
};

export type SelectedSource = {
  id: string;
  name: string;
  entity_cols: string[];
  target_cols: string[];
};

export default function DataAndIntegrations() {
  // const access_token_indexhub_api = useAuth0AccessToken();
  const { sendMessage, lastMessage, readyState } = useWebSocket(
    `${process.env.REACT_APP__FASTAPI__WEBSOCKET_DOMAIN}/sources/ws`
  );
  const [sources, setSources] = useState<Source[] | null>(null);
  const [userIntegrations, setUserIntegrations] = useState<Record<string, any>[] | null>(null)
  const [applyingIntegrations, setApplyingIntegrations] = useState(false)

  const [wsCallStarted, setWsCallStarted] = useState(false);
  const user_details = useSelector((state: AppState) => state.reducer?.user);
  const access_token_indexhub_api = useAuth0AccessToken();
  const toast = useToast();
  const {
    isOpen: isOpenNewSourceModal,
    onOpen: onOpenNewSourceModal,
    onClose: onCloseNewSourceModal
  } = useDisclosure()
  const {
    isOpen: isOpenNewIntegrationModal,
    onOpen: onOpenNewIntegrationModal,
    onClose: onCloseNewIntegrationModal
  } = useDisclosure()

  const getSourcesByUserId = () => {
    sendMessage(JSON.stringify({ user_id: user_details.id }));
  };

  const getUserIntegrationsApi = async () => {
    const userIntegrations = await getUserIntegrations(user_details.id, access_token_indexhub_api)
    if (Object.keys(userIntegrations).includes("user_integrations")) {
      setUserIntegrations(userIntegrations["user_integrations"])
    }

  }

  useEffect(() => {
    if (access_token_indexhub_api && user_details.id) {
      getUserIntegrationsApi()
    }
  }, [access_token_indexhub_api, user_details])

  useEffect(() => {
    if (user_details.id && readyState == ReadyState.OPEN && !wsCallStarted) {
      getSourcesByUserId();
      setWsCallStarted(true);
    }
  }, [user_details, readyState, wsCallStarted]);

  useEffect(() => {
    if (lastMessage?.data) {
      const sources: Record<"sources", Source[]> = JSON.parse(lastMessage.data);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      sources["sources"].map((source: Record<string, any>) => {
        source["data_fields"] = JSON.parse(source["data_fields"]);
        source["conn_fieldls"] = JSON.parse(source["conn_fields"]);
      });
      setSources(sources["sources"]);

      if (Object.keys(JSON.parse(lastMessage.data)).includes("sources")) {
        const statuses: string[] = [];
        const sources: Source[] = JSON.parse(lastMessage.data).sources;
        sources.forEach((source) => {
          statuses.push(source.status);
        });
        if (statuses.includes("RUNNING")) {
          setTimeout(getSourcesByUserId, 5000);
        }
      }
    }
  }, [lastMessage]);

  const submitUserIntegrations = async (user_integration_ids: number[]) => {
    setApplyingIntegrations(true)
    const submit_user_integrations_response = await setUserIntegrationsApi(
      user_details.id,
      user_integration_ids,
      access_token_indexhub_api
    )

    if (Object.keys(submit_user_integrations_response).includes("ok")) {
      Toast(
        toast,
        "Integrations Applied",
        `Your chosen integrations will be automatically applied in your objectives`,
        "success"
      );
      getUserIntegrationsApi()
    } else {
      Toast(toast, "Error", "Something went wrong while applying your integrations. Please contact us for help", "error");
    }
    setApplyingIntegrations(false)
  }

  return (
    <>
      <VStack width="100%" spacing="8">
        <Text fontSize="2xl" fontWeight="bold" width="100%" textAlign="left">
          Data Sources
        </Text>
        <HStack width="100%" justify="space-between">
          <Card p="1rem" width="49%" cursor="pointer" onClick={() => { onOpenNewSourceModal() }}>
            <HStack height="100%">
              <VStack height="100%" alignItems="flex-start" justify="space-between">
                <VStack mb="6" alignItems="flex-start">
                  <Flex p="1rem" mb="2" border="1px solid #eeeef1" borderRadius="8">
                    <FontAwesomeIcon icon={faDatabase as any} />
                  </Flex>
                  <Heading fontSize="md">New data source</Heading>
                  <Text color="text.gray">Connect to your data from multiple sources</Text>
                </VStack>
                <Button>Create new</Button>
              </VStack>
            </HStack>
          </Card>
          <Card p="1rem" width="49%" cursor="pointer" onClick={() => { onOpenNewIntegrationModal() }}>
            <HStack height="100%">
              <VStack height="100%" alignItems="flex-start" justify="space-between">
                <VStack mb="6" alignItems="flex-start">
                  <Flex p="1rem" border="1px solid #eeeef1" borderRadius="8">
                    <FontAwesomeIcon icon={faArrowsToCircle as any}></FontAwesomeIcon>
                  </Flex>
                  <Heading fontSize="md">New integration</Heading>
                  <Text color="text.gray">
                    Integrate external datasets to improve your forecasts
                  </Text>
                </VStack>
                <Button>
                  Create new
                </Button>
              </VStack>
            </HStack>
          </Card>
        </HStack>
        <Tabs width="100%" mt="6" variant="line">
          <TabList width="100%" justifyContent="left">
            <Tab><Text>Data Sources</Text></Tab>
            <Tab><Text>Integrations</Text></Tab>
          </TabList>
          <TabPanels>
            <TabPanel px="unset">
              {sources ? (
                sources.length > 0 ? (
                  <Grid templateColumns="repeat(3, 1fr)" gap={6}>
                    {sources.map((source, idx) => {
                      return (
                        <Card key={idx} p="1rem">
                          <Stack>
                            <HStack width="100%" justify="space-between" alignItems="flex-start">
                              <Flex width="2.5rem" height="2.5rem" p="5px" border="1px solid #eeeef1" borderRadius="8">
                                {logos[source.tag]}
                              </Flex>
                              <HStack>
                                <FontAwesomeIcon
                                  size="2xs"
                                  icon={faCircleDot as any}
                                  beatFade
                                  style={{
                                    color: status_colors[source.status]
                                  }}
                                />
                                <Text
                                  textAlign="center"
                                  fontSize="2xs"
                                  color={status_colors[source.status]}
                                >
                                  {source.status}
                                </Text>
                              </HStack>
                            </HStack>
                            <VStack alignItems="flex-start">
                              <Text>
                                {source.name}
                              </Text>
                              <Text fontSize="xs" color="text.gray" mt="unset !important">
                                Last updated: {new Date(source.updated_at).toLocaleString()}
                              </Text>
                            </VStack>
                            <HStack>
                              <Flex p="5px" border="1px solid #eeeef1" borderRadius="5">
                                <FontAwesomeIcon size="xs" color="#797986" icon={faDatabase as any} />
                              </Flex>
                              <Flex p="5px" border="1px solid #eeeef1" borderRadius="5">
                                <FontAwesomeIcon size="xs" color="#797986" icon={faDatabase as any} />
                              </Flex>
                            </HStack>
                          </Stack>
                        </Card>
                      )
                    })}
                  </Grid>
                ) : (
                  <Stack alignItems="center" justifyContent="center" height="full">
                    <Text>No sources found</Text>
                  </Stack>
                )
              ) : (
                <Stack alignItems="center" justifyContent="center" height="full">
                  <Spinner />
                  <Text>Loading...</Text>
                </Stack>
              )}
            </TabPanel>
            <TabPanel px="unset">
              {userIntegrations ? (
                userIntegrations.length > 0 ? (
                  <Grid templateColumns="repeat(3, 1fr)" gap={6}>
                    {userIntegrations.map((integration, idx) => {
                      return (
                        <Card key={idx} p="1rem">
                          <Stack>
                            <VStack alignItems="flex-start">
                              <Text>
                                {integration["name"]}
                              </Text>
                              <Text fontSize="xs" color="text.gray" mt="unset !important">
                                {integration["description"]}
                              </Text>
                              <Text fontSize="xs" color="text.gray" mt="unset !important">
                                Last Updated: {new Date(integration["updated_at"]).toLocaleString()}
                              </Text>
                            </VStack>
                          </Stack>
                        </Card>
                      )
                    })}
                  </Grid>
                ) : (
                  <Stack alignItems="center" justifyContent="center" height="full">
                    <Text>No integrations found</Text>
                  </Stack>
                )
              ) : (
                <Stack alignItems="center" justifyContent="center" height="full">
                  <Spinner />
                  <Text>Loading...</Text>
                </Stack>
              )}
            </TabPanel>
          </TabPanels>
        </Tabs>

      </VStack>
      <Modal size="6xl" isOpen={isOpenNewSourceModal} onClose={onCloseNewSourceModal}>
        <ModalOverlay />
        <ModalContent>
          <ModalCloseButton />
          <ModalBody>
            <NewSource onCloseNewSourceModal={onCloseNewSourceModal} />
          </ModalBody>
        </ModalContent>
      </Modal>
      <Modal size="6xl" isOpen={isOpenNewIntegrationModal} onClose={onCloseNewIntegrationModal}>
        <ModalOverlay />
        <ModalContent>
          <ModalCloseButton />
          <ModalBody>
            <NewIntegration userIntegrations={userIntegrations} submitUserIntegrations={submitUserIntegrations} applyingIntegrations={applyingIntegrations} />
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
}
