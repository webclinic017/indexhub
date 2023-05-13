import { Box, Button, Checkbox, CheckboxGroup, Grid, HStack, Spinner, Stack, Text, VStack } from "@chakra-ui/react";
import React, { useEffect, useState } from "react"
import { AppState } from "../..";
import { useSelector } from "react-redux";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { getAllIntegrations } from "../../utilities/backend_calls/integration";
import { Card } from "@chakra-ui/card";

const NewIntegration = (props: {
    userIntegrations: Record<string, any>[] | null,
    submitUserIntegrations: (user_integration_ids: number[]) => Promise<void>
    applyingIntegrations: boolean
}) => {

    const [allIntegrations, setAllIntegrations] = useState<Record<string, any>[] | null>(null)
    const [selectedIntegrationIds, setSelectedIntegrationIds] = useState<number[] | null>(null)

    const user_details = useSelector((state: AppState) => state.reducer?.user);
    const access_token_indexhub_api = useAuth0AccessToken();

    useEffect(() => {
        const getAllIntegrationsApi = async () => {
            const allIntegrations = await getAllIntegrations(access_token_indexhub_api)
            if (Object.keys(allIntegrations).includes("integrations")) {
                setAllIntegrations(allIntegrations["integrations"])
            }
        }

        if (access_token_indexhub_api && user_details.id) {
            getAllIntegrationsApi()
        }
    }, [access_token_indexhub_api, user_details])


    useEffect(() => {
        if (props.userIntegrations) {
            const user_integration_ids = props.userIntegrations.map(integration => integration["id"])
            setSelectedIntegrationIds([...user_integration_ids])
        }
    }, [props.userIntegrations])

    return (
        <Stack>
            <Text fontSize="2xl" fontWeight="bold" textAlign="left">
                All Integrations
            </Text>
            <Text mt="unset !important" fontSize="xs" textAlign="left">
                Choose your desired integration(s) to be used in your objectives
            </Text>
            {(selectedIntegrationIds && allIntegrations) ? (
                <CheckboxGroup colorScheme='green' value={selectedIntegrationIds} onChange={(e) => { setSelectedIntegrationIds([...(e.map(Number))]) }}>
                    <Box overflowY="scroll" maxH="30rem" p="5px">
                        <Grid templateColumns="repeat(3, 1fr)" gap={6}>
                            {allIntegrations.map((integration, idx) => {
                                return (
                                    <Card key={idx} p="1rem">
                                        <Stack>
                                            <HStack width="100%" justify="flex-end">
                                                <Checkbox disabled={integration["status"] != "SUCCESS"} value={integration["id"]} />
                                            </HStack>
                                            <VStack alignItems="flex-start">
                                                <Text>
                                                    {integration["name"]}
                                                </Text>
                                                <Text fontSize="xs" color="text.grey" mt="unset !important">
                                                    {integration["description"]}
                                                </Text>
                                                <Text fontSize="xs" color="text.grey" mt="unset !important">
                                                    Last Updated: {new Date(integration["updated_at"]).toLocaleString()}
                                                </Text>
                                            </VStack>
                                        </Stack>
                                    </Card>
                                )
                            })}
                        </Grid>
                    </Box>
                </CheckboxGroup>
            ) : (
                <Stack alignItems="center" justifyContent="center" height="full">
                    <Spinner />
                    <Text>Loading...</Text>
                </Stack>
            )}
            <hr style={{ width: "100%", margin: "1rem 0" }}></hr>
            <HStack mt="unset !important" pb="1rem" width="100%" justify="flex-end">
                <Button isLoading={props.applyingIntegrations} loadingText="Applying integrations..." onClick={() => { props.submitUserIntegrations(selectedIntegrationIds ? selectedIntegrationIds : []) }}>
                    Apply Integrations
                </Button>
            </HStack>
        </Stack>
    );
}

export default NewIntegration