import React, { useEffect, useState} from "react";
import { Container, Text, VStack, Box, Stack, Heading, Button, HStack, TableContainer, useDisclosure, Modal, ModalOverlay, ModalContent, ModalHeader, ModalCloseButton, ModalBody, ModalFooter, useToast } from '@chakra-ui/react'
import { useAuth0AccessToken } from "../../utilities/hooks/auth0"
import { useSelector } from "react-redux";
import { AppState } from "../../index";
import { deleteSource, getSource } from "../../utilities/backend_calls/source";
import { Link } from "react-router-dom"
import { createColumnHelper } from "@tanstack/react-table";
import { DataTable } from "../../components/table";
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPlus, faTrash,
} from "@fortawesome/free-solid-svg-icons";
import NewReport from "../reports/new_report";
import { createReport as createReportApi } from "../../utilities/backend_calls/report";
import Toast from "../../components/toast";


export type Source = {
    id: string,
    s3_data_bucket: string,
    raw_data_path: string,
    manual_forecast_path: string,
    freq: string,
    time_col: string,
    target_cols: string[],
    entity_cols: string[],
    filters: string[],
    created_at: string,
    updated_at: string,
    start_date: string,
    end_date: string,
    name: string,
    user_id: string,
    fct_panel_paths: string,
    status: string,
    msg: string,
}

type SelectedSource = {
  id: string
  name: string,
  entity_cols: string[],
  target_cols: string[],
}


export default function SourcesTable() {

    const access_token_indexhub_api = useAuth0AccessToken()
    const [sources, setSources] = useState<{sources: Source[]}>({sources: []})
    const [selectedSource, setSelectedSource] = useState<SelectedSource>({id: "", name: "", entity_cols: [], target_cols: []})

    const [selectedLevelCols, setSelectedLevelCols] = useState([])
    const [selectedTargetCol, setSelectedTargetCol] = useState("")

    const navigate = useNavigate();
    const { isOpen, onOpen, onClose } = useDisclosure()
    const toast = useToast()

    const user_details = useSelector(
        (state: AppState) => state.reducer?.user
    );

    useEffect(() => {
        const getReportByUserId = async () => {
          const sources_response = await getSource(user_details.user_id, "", access_token_indexhub_api)
          if (Object.keys(sources_response).includes("sources")){
            setSources(sources_response)
          }
        }
        if (access_token_indexhub_api && user_details.user_id) {
          getReportByUserId()
        }
    }, [user_details, access_token_indexhub_api])

    const openNewReportModal = (source_id: string, source_name: string, entity_cols: string[], target_cols: string[]) => {
      setSelectedSource({id: source_id, name: source_name, entity_cols, target_cols})
      onOpen()
    }

    const createReport = async () => {
      if (selectedLevelCols.length > 0 && selectedTargetCol) {
        const response = await createReportApi(user_details.user_id, selectedSource.name, selectedLevelCols, selectedTargetCol, selectedSource.id, access_token_indexhub_api)
        if (Object.keys(response).includes("report_id")) {
          navigate("/reports")
        } else {
          Toast(toast, "Error", response["detail"], "error")
        }
      } else {
        Toast(toast, "Empty / Invalid Columns", "Please ensure all required columns are filled with valid values", "error")
      }
    }

    const columnHelper = createColumnHelper<Source>();

    const columns = [
        columnHelper.accessor("name", {
            cell: (info) => info.getValue(),
            header: "Name"
        }),
        columnHelper.accessor(row => [row.s3_data_bucket, row.raw_data_path, row.manual_forecast_path], {
            id: "paths",
            cell: (info) => <VStack alignItems="flex-start">
                                <Text><b>Raw Data:</b> s3://{info.getValue()[0]}/{info.getValue()[1]}</Text>
                                <Text><b>Manual Forecast:</b> s3://{info.getValue()[0]}/{info.getValue()[2]}</Text>
                            </VStack>,
            header: "Paths"
          }),
        columnHelper.accessor((row: any) => [row.time_col, row.target_cols, row.entity_cols], {
        id: "columns",
        cell: (info) => <VStack alignItems="flex-start">
                            <Text><b>Time Col:</b> {info.getValue()[0]}</Text>
                            <Text><b>Target Col(s):</b> {info.getValue()[1].join(", ")}</Text>
                            <Text><b>Entity Col(s):</b> {info.getValue()[2].join(", ")}</Text>
                        </VStack>,
        header: "Columns"
        }),
        columnHelper.accessor("status", {
          cell: (info) => info.getValue(),
          header: "Status",
          meta:{
            isBadge: true
          }
        }),
        columnHelper.accessor((row: any) => [row.id, row.name, row.entity_cols, row.target_cols, row.status], {
          id: "id",
          cell: (info) => {
            return (
              <HStack justifyContent="space-between" width="60px">
                  {/* Need to be changed to new reports instead */}
                  <FontAwesomeIcon cursor="pointer" icon={faPlus} onClick={() => {
                    if (info.getValue()[4] == "COMPLETE") {
                      openNewReportModal(info.getValue()[0], info.getValue()[1], info.getValue()[2], info.getValue()[3])
                    }
                  }}/> 
                  <FontAwesomeIcon cursor="pointer" icon={faTrash} onClick={async () => setSources(await deleteSource(access_token_indexhub_api, info.getValue()[0]))}/>
              </HStack>
            )
          },
          header: "",
          meta:{
            isButtons: true,
          },
          enableSorting: false,
        }),
      ];

    return (
      <>
        <VStack width="100%" padding="10px">
            {sources?.sources?.length > 0 ? 
                <TableContainer width="100%" backgroundColor="white">
                    <DataTable columns={columns} data={sources.sources} body_height="73px"></DataTable>
                </TableContainer>
            : (
                <Box width="100%" as="section" bg="bg-surface">
                    <Container maxWidth="unset" py={{ base: '16', md: '24' }}>
                        <Stack spacing={{ base: '8', md: '10' }}>
                        <Stack spacing={{ base: '4', md: '5' }} align="center">
                            <Heading>Ready to Grow?</Heading>
                            <Text  color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                            With these comprehensive reports you will be able to analyse the past with statistical context and look into the future of what you care most!
                            </Text>
                        </Stack>
                        <Stack spacing="3" direction={{ base: 'column', sm: 'row' }} justify="center">
                            <Button as={Link} colorScheme="facebook" size="lg" to="/sources/new_source">
                                Create Source
                            </Button>
                        </Stack>
                        </Stack>
                    </Container>
                </Box>
            )}
        </VStack>
        <Modal isOpen={isOpen} onClose={onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>New Report</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <NewReport source_name={selectedSource.name} entity_cols={selectedSource.entity_cols} target_cols={selectedSource.target_cols} setSelectedLevelCols={setSelectedLevelCols} setSelectedTargetCol={setSelectedTargetCol}/>
            </ModalBody>
            <ModalFooter>
              <Button colorScheme='blue' mr={3} onClick={createReport}>Create Report</Button>
              <Button variant="ghost" onClick={onClose}>
                Close
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </>
    )
}