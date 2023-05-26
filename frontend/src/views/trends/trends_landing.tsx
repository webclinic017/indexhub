import { Badge, Box, Button, Divider, HStack, Heading, Select, Stack, Text, Tooltip, VStack, useDisclosure } from "@chakra-ui/react"
import React, { useEffect } from "react"
import ChatBot from "./chat_bot"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faChevronDoubleLeft, faChevronLeft } from "@fortawesome/pro-light-svg-icons"
import Projector from "./projector"
import { useChatContext } from "../chat/chat_context"
import { useTrendsContext } from "./trends_context"


const MAX_CHARTS = 2;

// const stats = [
//     { label: 'Total Subscribers', value: '71,887', delta: { value: '320', isUpwardsTrend: true } },
//     { label: 'Avg. Open Rate', value: '56.87%', delta: { value: '2.3%', isUpwardsTrend: true } },
//     { label: 'Avg. Click Rate', value: '12.87%', delta: { value: '0.1%', isUpwardsTrend: false } },
//     { label: 'Total Subscribers', value: '71,887', delta: { value: '320', isUpwardsTrend: true } },
//     { label: 'Avg. Open Rate', value: '56.87%', delta: { value: '2.3%', isUpwardsTrend: true } },
//     { label: 'Avg. Click Rate', value: '12.87%', delta: { value: '0.1%', isUpwardsTrend: false } },
//     { label: 'Total Subscribers', value: '71,887', delta: { value: '320', isUpwardsTrend: true } },
//     { label: 'Avg. Open Rate', value: '56.87%', delta: { value: '2.3%', isUpwardsTrend: true } },
//     { label: 'Avg. Click Rate', value: '12.87%', delta: { value: '0.1%', isUpwardsTrend: false } },
//     { label: 'Total Subscribers', value: '71,887', delta: { value: '320', isUpwardsTrend: true } },
//     { label: 'Avg. Open Rate', value: '56.87%', delta: { value: '2.3%', isUpwardsTrend: true } },
//     { label: 'Avg. Click Rate', value: '12.87%', delta: { value: '0.1%', isUpwardsTrend: false } },
//     { label: 'Total Subscribers', value: '71,887', delta: { value: '320', isUpwardsTrend: true } },
//     { label: 'Avg. Open Rate', value: '56.87%', delta: { value: '2.3%', isUpwardsTrend: true } },
//     { label: 'Avg. Click Rate', value: '12.87%', delta: { value: '0.1%', isUpwardsTrend: false } },
//     { label: 'Total Subscribers', value: '71,887', delta: { value: '320', isUpwardsTrend: true } },
//     { label: 'Avg. Open Rate', value: '56.87%', delta: { value: '2.3%', isUpwardsTrend: true } },
//     { label: 'Avg. Click Rate', value: '12.87%', delta: { value: '0.1%', isUpwardsTrend: false } },
// ]

const getTrendsList = async (apiToken: string): Promise<TrendsListItemProps[]> => {
    const url = `${process.env.REACT_APP__FASTAPI__DOMAIN}/trends/public`;
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiToken}`
        }
    });
    const data = await response.json() as Record<string, any>;
    console.log(`trendsList: ${JSON.stringify(data)}:${typeof data}`);

    const trendsList = Object.entries(data).map(([dataset_id, metadata]) => {
        return (
            {
                "dataset_id": dataset_id,
                "dataset_name": metadata["dataset_name"],
                "value": metadata["entity_count"],
                "entities": metadata["entities"],
                "delta": {
                    "value": metadata["entity_count"],
                    "isUpwardsTrend": true
                }
            } as TrendsListItemProps
        )
    });
    return trendsList;
}

const TrendsLanding = () => {
    const { trendsList, setTrendsList, apiToken } = useTrendsContext();
    const { onOpenChatBot, isOpenChatBot, onCloseChatBot } = useChatContext();
    useEffect(() => {
        const initAsync = async () => {
            const trendsListData = await getTrendsList(apiToken);
            setTrendsList(trendsListData);
        }
        if (!apiToken) {
            return;
        }
        initAsync();
    }, [apiToken]);


    return (
        <>
            <HStack width="100%" height="100%">
                <VStack width="25%" height="100%" overflowX="scroll">
                    {trendsList.map((props, idx) => <TrendsListItem key={idx} {...props} />)}
                </VStack>
                <VStack width="75%" height="100%" align="center">
                    <HStack width="100%" justify="flex-end">
                        <Tooltip label="View Trends" placement="left">
                            <Stack cursor="pointer" alignItems="center" justify="center" backgroundColor="buttons.gray" width="2rem" height="2rem" borderRadius={5} onClick={() => {
                                onOpenChatBot()
                            }}>
                                <FontAwesomeIcon icon={faChevronDoubleLeft} />
                            </Stack>
                        </Tooltip>
                    </HStack>
                    <VStack width="100%" height="100%" justify="center">
                        <Projector />
                    </VStack>
                </VStack>
            </HStack >

            <ChatBot isOpen={isOpenChatBot} onClose={onCloseChatBot} onOpen={onOpenChatBot} />
        </>
    )
}

export interface TrendsListItemProps {
    dataset_id: string
    dataset_name: string
    value: string
    entities: string[]
    delta: {
        value: string,
        isUpwardsTrend: boolean
    }
}

const TrendsListItem = (props: TrendsListItemProps) => {
    const { dataset_id, dataset_name, value } = props;
    const { setDatasetId } = useTrendsContext();
    return (
        <Box width="100%" bg="cards.background" borderRadius="lg" boxShadow="sm">
            <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
                <Stack>
                    <HStack justify="space-between">
                        <Text fontSize="2xl" color="muted">
                            {dataset_name}
                        </Text>
                        {/* <Icon as={FiMoreVertical} boxSize="5" color="muted" /> */}
                    </HStack>
                    <HStack justify="space-between">
                        <Heading size={{ base: 'sm', md: 'md' }}>{value}</Heading>
                        {/* <Badge variant="subtle" colorScheme={delta.isUpwardsTrend ? 'green' : 'red'}>
                                    <HStack spacing="1">
                                        <Icon as={delta.isUpwardsTrend ? FiArrowUpRight : FiArrowDownRight} />
                                        <Text>{delta.value}</Text>
                                    </HStack>
                                </Badge> */}
                    </HStack>
                </Stack>
            </Box>
            <Divider />
            <Box px={{ base: '4', md: '6' }} py="4">
                <Button variant="link" colorScheme="blue" size="sm" onClick={() => setDatasetId(dataset_id)}>
                    View embeddings
                </Button>
                <TrendEntitiesSelector {...props} />
            </Box>
        </Box>
    )
}


const TrendEntitiesSelector = (props: TrendsListItemProps) => {
    const { entities } = props;
    return <Select variant='filled'>
        {entities.map((entity_id, index) => (
            <option key={index} value={entity_id}>{entity_id}</option>
        ))}
    </Select>;
}

export default TrendsLanding