import React, { useState, useEffect } from "react";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { AppState } from "../../index";
import { useSelector } from "react-redux";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { deleteReport } from "../../utilities/backend_calls/report";
import {
  Button,
  TableContainer,
  VStack,
  HStack,
  Container,
  Box,
  Heading,
  Progress,
  Stack,
  Text,
  useColorModeValue,
  SimpleGrid,
} from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { createColumnHelper } from "@tanstack/react-table";
import { DataTable } from "../../components/table";
import { Link, useNavigate } from "react-router-dom";

export type Report = {
  id: string;
  source_id: string;
  source_name: string;
  entities: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  target_col: string;
  level_cols: string[];
  user_id: string;
  chart_id: string;
  table_id: string;
  status: string;
  created_at: string;
  completed_at: string;
};

export default function Reports() {
  const access_token_indexhub_api = useAuth0AccessToken();
  const { sendMessage, lastMessage, readyState } = useWebSocket(
    "ws://localhost:8000/reports/ws"
  );
  const [reports, setReports] = useState<{ reports: Report[] }>({
    reports: [],
  });
  const [current_pagination, setCurrentPagination] = useState(1);
  const [wsCallStarted, setWsCallStarted] = useState(false);
  const navigate = useNavigate();

  const stats = [
    {
      label: "Complete",
      value: reports?.reports?.reduce(
        (n, report) => n + Number(report.status === "COMPLETE"),
        0
      ),
      limit: reports?.reports?.length,
      color: "green",
    },
    {
      label: "Running",
      value: reports?.reports?.reduce(
        (n, report) => n + Number(report.status === "RUNNING"),
        0
      ),
      limit: reports?.reports?.length,
      color: "yellow",
    },
    {
      label: "Failed",
      value: reports?.reports?.reduce(
        (n, report) => n + Number(report.status === "FAILED"),
        0
      ),
      limit: reports?.reports?.length,
      color: "red",
    },
  ];

  const user_details = useSelector((state: AppState) => state.reducer?.user);

  const getReportsByUserId = () => {
    sendMessage(JSON.stringify({ user_id: user_details.user_id }));
  };

  const reports_per_page = 5;
  const start_index = (current_pagination - 1) * reports_per_page;
  const pages_required = Math.ceil(reports.reports?.length / reports_per_page);

  useEffect(() => {
    if (
      user_details.user_id &&
      readyState == ReadyState.OPEN &&
      !wsCallStarted
    ) {
      getReportsByUserId();
      setWsCallStarted(true);
    }
  }, [user_details, readyState, wsCallStarted]);

  useEffect(() => {
    if (lastMessage?.data) {
      setReports(JSON.parse(lastMessage.data));

      if (Object.keys(JSON.parse(lastMessage.data)).includes("reports")) {
        const statuses: string[] = [];
        const reports: Report[] = JSON.parse(lastMessage.data).reports;
        reports.forEach((report) => {
          statuses.push(report.status);
        });
        if (statuses.includes("RUNNING")) {
          setTimeout(getReportsByUserId, 5000);
        }
      }
    }
  }, [lastMessage]);

  const columnHelper = createColumnHelper<Report>();

  const columns = [
    columnHelper.accessor((row) => [row.source_name, row.id], {
      id: "source_name",
      cell: (info) => (
        <Text
          onClick={() => navigate(`/reports/${info.getValue()[1]}`)}
          cursor="pointer"
        >
          {info.getValue()[0]}
        </Text>
      ),
      header: "Source",
    }),
    columnHelper.accessor("target_col", {
      cell: (info) => info.getValue(),
      header: "Target",
    }),
    columnHelper.accessor("level_cols", {
      cell: (info) => info.getValue().join(", "),
      header: "Levels",
    }),
    columnHelper.accessor("created_at", {
      cell: (info) => new Date(info.getValue()).toLocaleString(),
      header: "Created at",
    }),
    columnHelper.accessor("completed_at", {
      cell: (info) => {
        if (info.getValue()) {
          return new Date(info.getValue()).toLocaleString();
        } else return "";
      },
      header: "Completed at",
    }),
    columnHelper.accessor("status", {
      cell: (info) => info.getValue(),
      header: "Status",
      meta: {
        isBadge: true,
      },
    }),
    columnHelper.accessor((row) => [row.id, row.source_id], {
      id: "reports",
      cell: (info) => {
        return (
          <VStack justifyContent="space-between" width="150px">
            <Button
              fontSize="small"
              width="150px"
              cursor="pointer"
              onClick={() => navigate(`/reports/${info.getValue()[0]}`)}
            >
              Predictions
            </Button>
            <Button
              fontSize="small"
              width="150px"
              cursor="pointer"
              onClick={() =>
                navigate(`/reports/profiling/${info.getValue()[1]}`)
              }
            >
              Data Quality
            </Button>
          </VStack>
        );
      },
      header: "Reports",
      meta: {
        isButtons: true,
      },
      enableSorting: false,
    }),
    columnHelper.accessor((row) => row.id, {
      id: "id",
      cell: (info) => {
        return (
          <HStack justifyContent="space-between" width="20px">
            <FontAwesomeIcon
              cursor="pointer"
              icon={faTrash}
              onClick={async () =>
                setReports(
                  await deleteReport(access_token_indexhub_api, info.getValue())
                )
              }
            />
          </HStack>
        );
      },
      header: "",
      meta: {
        isButtons: true,
      },
      enableSorting: false,
    }),
  ];

  return (
    <VStack padding="10px">
      <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">
        Reports
      </Text>
      {reports?.reports?.length > 0 ? (
        <>
          <VStack
            backgroundColor="white"
            width="100%"
            borderRadius="8px"
            box-shadow="0px 0px 1px rgba(48, 49, 51, 0.05),0px 2px 4px rgba(48, 49, 51, 0.1)"
          >
            <Container margin="1rem 0 4rem" maxWidth="unset">
              <SimpleGrid
                columns={{ base: 1, md: 3 }}
                gap={{ base: "5", md: "6" }}
              >
                {stats.map((stat, id) => {
                  return (
                    <Box
                      key={id}
                      bg="bg-surface"
                      boxShadow={useColorModeValue("sm", "sm-dark")}
                    >
                      <Box
                        px={{ base: "4", md: "6" }}
                        py={{ base: "5", md: "6" }}
                      >
                        <Stack>
                          <Text fontSize="sm">{stat.label}</Text>
                          <Stack direction="row" align="baseline">
                            <Heading>{stat.value}</Heading>
                            <Text aria-hidden fontWeight="semibold">
                              / {stat.limit}
                            </Text>
                          </Stack>
                        </Stack>
                      </Box>
                      <Progress
                        value={(stat.value / stat.limit) * 100}
                        size="xs"
                        borderRadius="none"
                        colorScheme={stat.color}
                        bg="bg-surface"
                      />
                    </Box>
                  );
                })}
              </SimpleGrid>
            </Container>

            <TableContainer width="100%" backgroundColor="white">
              <DataTable
                columns={columns}
                data={reports.reports.slice(
                  start_index,
                  start_index + reports_per_page
                )}
                body_height="73px"
              ></DataTable>
            </TableContainer>

            <HStack
              padding="0 25px"
              marginTop="20px !important"
              marginBottom="20px !important"
              justifyContent="space-between"
              width="100%"
            >
              <Text fontSize="sm">
                Showing {current_pagination} of {pages_required} pages
              </Text>
              <HStack>
                <Button
                  onClick={() => setCurrentPagination(current_pagination - 1)}
                  isDisabled={current_pagination == 1}
                >
                  Previous
                </Button>
                <Button
                  onClick={() => setCurrentPagination(current_pagination + 1)}
                  isDisabled={current_pagination == pages_required}
                >
                  Next
                </Button>
              </HStack>
            </HStack>
          </VStack>
        </>
      ) : (
        <Box width="100%" as="section" bg="bg-surface">
          <Container maxWidth="unset" py={{ base: "16", md: "24" }}>
            <Stack spacing={{ base: "8", md: "10" }}>
              <Stack spacing={{ base: "4", md: "5" }} align="center">
                <Heading>Ready to Grow?</Heading>
                <Text color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                  With these comprehensive reports you will be able to analyse
                  the past with statistical context and look into the future of
                  what you care most!
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
                  to="/sources"
                >
                  Create Report
                </Button>
              </Stack>
            </Stack>
          </Container>
        </Box>
      )}
    </VStack>
  );
}
