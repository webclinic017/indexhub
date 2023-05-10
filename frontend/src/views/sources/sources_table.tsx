import React, { useEffect, useState } from "react";
import {
  Container,
  Text,
  VStack,
  Box,
  Stack,
  Heading,
  Button,
  TableContainer,
  Flex,
  HStack,
} from "@chakra-ui/react";
// import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { AppState } from "../../index";
// import { deleteSource } from "../../utilities/backend_calls/source";
import { Link, useNavigate } from "react-router-dom";
import { createColumnHelper } from "@tanstack/react-table";
import { DataTable } from "../../components/table";
import { Card, CardBody } from "@chakra-ui/card";
import { capitalizeFirstLetter } from "../../utilities/helpers";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCalendarDays } from "@fortawesome/free-solid-svg-icons";
import { ReactComponent as S3Logo } from "../../assets/images/svg/s3.svg";
import { ReactComponent as AzureLogo } from "../../assets/images/svg/azure.svg";
import { faCircleDot } from "@fortawesome/free-regular-svg-icons";
import { colors } from "../../theme/theme";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
// import { faTrash } from "@fortawesome/free-solid-svg-icons";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const logos: Record<string, any> = {
  s3: <S3Logo width="7rem" />,
  azure: <AzureLogo width="7rem" />,
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
  msg: string;
  target_cols: string; // to be removed when refactoring objectives
};

export type SelectedSource = {
  id: string;
  name: string;
  entity_cols: string[];
  target_cols: string[];
};

export default function SourcesTable() {
  // const access_token_indexhub_api = useAuth0AccessToken();
  const { sendMessage, lastMessage, readyState } = useWebSocket(
    `${process.env.REACT_APP_INDEXHUB_API_DOMAIN_WEBSOCKET}/sources/ws`
  );
  const [sources, setSources] = useState<{ sources: Source[] }>({
    sources: [],
  });
  const [wsCallStarted, setWsCallStarted] = useState(false);
  const navigate = useNavigate();
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  const getSourcesByUserId = () => {
    sendMessage(JSON.stringify({ user_id: user_details.id }));
  };

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
        source["columns"] = JSON.parse(source["columns"]);
        source["variables"] = JSON.parse(source["variables"]);
      });
      setSources(sources);

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

  const columnHelper = createColumnHelper<Source>();

  const columns = [
    columnHelper.accessor("name", {
      cell: (info) => info.getValue(),
      header: "Name",
    }),
    columnHelper.accessor(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (row: any) => [row.variables, row.output_path],
      {
        id: "paths",
        cell: (info) => (
          <VStack alignItems="flex-start">
            <Text>
              <b>Raw Data:</b> s3://{info.getValue()[0]["bucket_name"]}/
              {info.getValue()[0]["object_path"]}
            </Text>
            <Text>
              <b>Output path: {info.getValue()[1]}</b>
            </Text>
          </VStack>
        ),
        header: "Paths",
      }
    ),
    columnHelper.accessor(
      "columns", // eslint-disable-line @typescript-eslint/no-explicit-any
      {
        id: "columns",
        cell: (info) => (
          <VStack alignItems="flex-start">
            <Text>
              <b>Time Col:</b> {info.getValue()["time_col"]}
            </Text>
            <Text>
              <b>Feature Col(s):</b>{" "}
              {info.getValue()["feature_cols"].join(", ")}
            </Text>
            <Text>
              <b>Entity Col(s):</b> {info.getValue()["entity_cols"].join(", ")}
            </Text>
          </VStack>
        ),
        header: "Columns",
      }
    ),
    columnHelper.accessor("status", {
      cell: (info) => info.getValue(),
      header: "Status",
      meta: {
        isBadge: true,
      },
    }),
    // columnHelper.accessor(
    //   // eslint-disable-next-line @typescript-eslint/no-explicit-any
    //   (row: any) => [
    //     row.id,
    //     row.name,
    //     row.entity_cols,
    //     row.target_cols,
    //     row.status,
    //   ],
    //   {
    //     id: "id",
    //     cell: (info) => {
    //       return (
    //         <HStack justifyContent="space-between" width="60px">
    //           <FontAwesomeIcon
    //             cursor="pointer"
    //             icon={faTrash}
    //             onClick={async () =>
    //               setSources(
    //                 await deleteSource(
    //                   access_token_indexhub_api,
    //                   info.getValue()[0]
    //                 )
    //               )
    //             }
    //           />
    //         </HStack>
    //       );
    //     },
    //     header: "",
    //     meta: {
    //       isButtons: true,
    //     },
    //     enableSorting: false,
    //   }
    // ),
  ];

  return (
    <>
      <Flex width="100%" justifyContent="center">
        <Card boxShadow="md" borderRadius="lg" width="50%" p="6" backgroundColor="white">
          <CardBody>
            <HStack>
              <Text fontSize="small" fontWeight="bold" pr="2">
                Your Storage:
              </Text>
              <FontAwesomeIcon
                size="2xs"
                icon={faCircleDot}
                beatFade
                style={{
                  color: user_details.storage_bucket_name
                    ? colors.supplementary.indicators.main_green
                    : colors.supplementary.indicators.main_red,
                }}
              />
              <Text
                textAlign="center"
                fontSize="2xs"
                color={
                  user_details.storage_bucket_name
                    ? colors.supplementary.indicators.main_green
                    : colors.supplementary.indicators.main_red
                }
              >
                {user_details.storage_bucket_name
                  ? "CONFIGURED"
                  : "NOT CONFIGURED"}
              </Text>
            </HStack>
            {user_details.storage_bucket_name ? (
              <HStack justifyContent="center">
                <Box p="6">{logos[user_details.storage_tag]}</Box>

                <VStack alignItems="flex-start">
                  <Heading
                    size="md"
                    fontWeight="extrabold"
                    letterSpacing="tight"
                    marginEnd="6"
                  >
                    {capitalizeFirstLetter(user_details.storage_tag)} Storage
                  </Heading>
                  <Text mt="1" fontWeight="medium">
                    Bucket name: {user_details.storage_bucket_name}
                  </Text>
                  <Stack spacing="1" mt="2">
                    <HStack fontSize="sm">
                      <FontAwesomeIcon icon={faCalendarDays} />
                      <Text>
                        {new Date(
                          user_details.storage_created_at
                        ).toDateString()}
                      </Text>
                    </HStack>
                  </Stack>
                </VStack>
              </HStack>
            ) : (
              <Flex p="5" justify="center">
                <Button onClick={() => navigate("/new_storage")}>
                  Configure Storage
                </Button>
              </Flex>
            )}
          </CardBody>
        </Card>
      </Flex>
      <VStack width="100%" padding="10px">
        <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">
          Sources
        </Text>
        {sources?.sources?.length > 0 ? (
          <TableContainer width="100%" backgroundColor="white" borderRadius={8}>
            <DataTable
              columns={columns}
              data={sources.sources}
              body_height="73px"
            ></DataTable>
          </TableContainer>
        ) : (
          <Box width="100%" as="section" bg="bg-surface">
            <Container maxWidth="unset" py={{ base: "16", md: "24" }}>
              <Stack spacing={{ base: "8", md: "10" }}>
                <Stack spacing={{ base: "4", md: "5" }} align="center">
                  <Heading>Ready to Grow?</Heading>
                  <Text
                    color="muted"
                    maxW="2xl"
                    textAlign="center"
                    fontSize="xl"
                  >
                    With these comprehensive reports you will be able to analyse
                    the past with statistical context and look into the future
                    of what you care most!
                  </Text>
                </Stack>
                <Stack
                  spacing="3"
                  direction={{ base: "column", sm: "row" }}
                  justify="center"
                >
                  <Button
                    as={Link}
                    colorScheme="facebook"
                    size="lg"
                    to="/sources/new_source"
                  >
                    Create Source
                  </Button>
                </Stack>
              </Stack>
            </Container>
          </Box>
        )}
      </VStack>
    </>
  );
}
