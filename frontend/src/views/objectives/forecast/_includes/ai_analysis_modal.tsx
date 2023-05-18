import React, { useEffect, useState } from "react"
import { Box, HStack, Heading, Link, ListItem, Modal, ModalBody, ModalCloseButton, ModalContent, ModalHeader, ModalOverlay, Spinner, Stack, Tab, TabIndicator, TabList, TabPanel, TabPanels, Tabs, Text, UnorderedList } from "@chakra-ui/react"
import ReactEcharts from "echarts-for-react";
import { useWebSocket } from "react-use-websocket/dist/lib/use-websocket";
import { ReadyState } from "react-use-websocket";
import { capitalizeFirstLetter } from "../../../../utilities/helpers";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faLink } from "@fortawesome/pro-light-svg-icons";
import { Objective } from "../../objectives_dashboard";

const FREQ_TO_COPILOT_FREQ: Record<string, string> = {
    "Hourly": "1hr",
    "Daily": "1da",
    "Weekly": "1wk",
    "Monthly": "1mo",
}

const AiAnalysisModal = (props: {
    cutoff: any[],
    objective: Objective | null,
    isOpenTrendModal: boolean,
    onCloseTrendModal: () => void,
    chartFilter: Record<string, string[]>,
    entityTrendChart: Record<any, any> | null
}) => {
    const [answers, setAnswers] = useState<Record<string, any>[]>([])
    const [news, setNews] = useState<Record<string, any>[] | null>(null)
    const [analysis, setAnalysis] = useState<string[] | null>(null)
    const [sources, setSources] = useState<Record<string, any>[] | null>(null)
    const [questions, setQuestions] = useState<string[] | null>(null)

    const { sendMessage, lastMessage, readyState } = useWebSocket(
        `${process.env.REACT_APP__FASTAPI__WEBSOCKET_DOMAIN}/copilot/ws`, {
        shouldReconnect: (closeEvent) => true,
    }
    );

    const KEYS_TO_SETTERS: Record<string, React.Dispatch<React.SetStateAction<any>>> = {
        "answers": setAnswers,
        "news": setNews,
        "analysis": setAnalysis,
        "sources": setSources,
        "questions": setQuestions
    }

    useEffect(() => {
        if (props.isOpenTrendModal && readyState == ReadyState.OPEN && props.objective) {
            setAnswers([])
            setNews(null)
            setAnalysis(null)
            setSources(null)
            setQuestions(null)
            sendMessage(JSON.stringify({
                "user_id": props.objective["user_id"],
                "objective_id": props.objective["id"],
                "target_col": props.objective["fields"]["target_col"],
                "entity_col": props.objective["fields"]["level_cols"][0],
                "entity_id": props.chartFilter["entity"][0],
                "freq": FREQ_TO_COPILOT_FREQ[props.objective["fields"]["freq"]],
                "fh": props.objective["fields"]["fh"],
                "cutoff": props.cutoff[props.cutoff.length - 1]["Time"],
            }), true)
        }
    }, [props.isOpenTrendModal])

    useEffect(() => {
        if (lastMessage?.data) {
            const data = JSON.parse(lastMessage?.data)
            if (Object.keys(data).includes("answer")) {
                const internal_answers = answers
                internal_answers.push(data["answer"])
                setAnswers([...internal_answers])
            } else {
                KEYS_TO_SETTERS[Object.keys(data)[0]](data[Object.keys(data)[0]])
            }
        }
    }, [lastMessage])

    return (
        <Modal isOpen={props.isOpenTrendModal} onClose={props.onCloseTrendModal} size="6xl">
            <ModalOverlay />
            <ModalContent >
                <ModalHeader>
                </ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                    <Stack>
                        <HStack>
                            {Object.keys(props.chartFilter).map((filter_key, idx) => {
                                return (
                                    <Box
                                        key={idx}
                                        px={{ base: '4', md: '6' }}
                                        py={{ base: '5', md: '6' }}
                                        minWidth="15rem"
                                    >
                                        <Stack>
                                            <Text fontSize="sm" color="muted">
                                                {capitalizeFirstLetter(filter_key)}
                                            </Text>
                                            <Heading mt="unset !important" size="xl">{props.chartFilter[filter_key]}</Heading>
                                        </Stack>
                                    </Box>
                                )
                            })}
                        </HStack>
                        <Tabs mt="1.5rem" position="relative" variant="unstyled" isLazy lazyBehavior="keepMounted">
                            <TabList>
                                <Tab px={10} fontWeight="bold">Descriptive Analysis</Tab>
                                <Tab px={10} fontWeight="bold">Report</Tab>
                            </TabList>
                            <TabIndicator
                                mt="-1.5px"
                                height="2px"
                                bg="blue.500"
                                borderRadius="1px"
                            />
                            <TabPanels>
                                <TabPanel>
                                    <HStack alignItems="stretch">
                                        <Box my="1.5rem !important" width="65%" >
                                            {props.entityTrendChart ? (
                                                <ReactEcharts
                                                    option={props.entityTrendChart}
                                                    style={{
                                                        height: "100%",
                                                        width: "100%",
                                                    }}
                                                />
                                            ) : (
                                                <Stack alignItems="center" justifyContent="center" height="full">
                                                    <Spinner />
                                                    <Text>Loading...</Text>
                                                </Stack>
                                            )}

                                        </Box>
                                        <Box p="1rem" backgroundColor="#f9f9f9" width="35%" borderRadius={10} height="27rem" overflowY="scroll">
                                            <Stack height="100%">
                                                <Text fontWeight="bold">Descriptive Analysis</Text>
                                                {analysis ? (
                                                    <UnorderedList pl="1rem">
                                                        {analysis.map((analysis_point, idx) => {
                                                            return (
                                                                <ListItem fontSize="xs" key={idx}>
                                                                    {analysis_point}
                                                                </ListItem>
                                                            )
                                                        })}
                                                    </UnorderedList>
                                                ) : (
                                                    <Stack alignItems="center" justifyContent="center" height="full">
                                                        <Spinner />
                                                        <Text>Loading...</Text>
                                                    </Stack>
                                                )}
                                            </Stack>

                                        </Box>
                                    </HStack>
                                </TabPanel>
                                <TabPanel>
                                    <HStack py="1rem" height="30rem" overflowY="scroll" alignItems="flex-start">
                                        <Box width="70%" height="100%" mr="2rem">
                                            <Stack height="100%">
                                                {answers.length > 0 ? (
                                                    <>
                                                        {answers.map((answer, key) => {
                                                            return (
                                                                <Stack pb="1.5rem" key={key}>
                                                                    <Text textAlign="justify" fontWeight="bold" fontSize="xs">{answer["q"]}</Text>
                                                                    <Text textAlign="justify" fontSize="xs">{answer["a"]}</Text>
                                                                </Stack>
                                                            )
                                                        })}
                                                        {answers.length < answers[0]["n_parts"] && (
                                                            <Stack alignItems="center" justifyContent="center" height="full">
                                                                <Spinner />
                                                                <Text>Loading...</Text>
                                                            </Stack>
                                                        )}
                                                    </>
                                                ) : (
                                                    <Stack alignItems="center" justifyContent="center" height="full">
                                                        <Spinner />
                                                        <Text>Loading...</Text>
                                                    </Stack>
                                                )}
                                            </Stack>
                                        </Box>

                                        <Box width="30%" >
                                            <Stack>
                                                <Stack p="1rem" backgroundColor="#f9f9f9" borderRadius={10}>
                                                    <Text fontWeight="bold">Sources</Text>
                                                    {sources ? (
                                                        <>
                                                            {sources.map((source, key) => {
                                                                return (
                                                                    <Stack pb="1.5rem" key={key}>
                                                                        <HStack>
                                                                            <FontAwesomeIcon size="xs" icon={faLink as any} />
                                                                            <Text color="#848383" overflow="hidden" textOverflow="ellipsis" whiteSpace="nowrap" textAlign="justify" fontSize="xs">{source["url"]}</Text>
                                                                        </HStack>
                                                                        <Text fontWeight="bold" className="ellipsis-2" textAlign="justify" fontSize="xs">{source["query"]} | {source["title"]}</Text>
                                                                        <Link target="_blank" href={source["url"]} className="ellipsis-3" color="blue" mt="unset !important" textAlign="justify" fontSize="xs">{source["snippet"]}</Link>
                                                                    </Stack>
                                                                )
                                                            })}
                                                        </>
                                                    ) : (
                                                        <Stack alignItems="center" justifyContent="center" height="full">
                                                            <Spinner />
                                                            <Text>Loading...</Text>
                                                        </Stack>
                                                    )}
                                                </Stack>
                                                <Stack p="1rem" backgroundColor="#f9f9f9" borderRadius={10}>
                                                    <Text fontWeight="bold">News</Text>
                                                    {news ? (
                                                        <>
                                                            {news.map((idv_news, key) => {
                                                                return (
                                                                    <Stack pb="1.5rem" key={key}>
                                                                        <HStack>
                                                                            <FontAwesomeIcon size="xs" icon={faLink as any} />
                                                                            <Text color="#848383" overflow="hidden" textOverflow="ellipsis" whiteSpace="nowrap" textAlign="justify" fontSize="xs">{idv_news["url"]}</Text>
                                                                        </HStack>
                                                                        <Text fontWeight="bold" className="ellipsis-2" textAlign="justify" fontSize="xs">{idv_news["query"]} | {idv_news["title"]}</Text>
                                                                        <Link target="_blank" href={idv_news["url"]} className="ellipsis-3" color="blue" mt="unset !important" textAlign="justify" fontSize="xs">{idv_news["description"]}</Link>
                                                                    </Stack>
                                                                )
                                                            })}
                                                        </>
                                                    ) : (
                                                        <Stack alignItems="center" justifyContent="center" height="full">
                                                            <Spinner />
                                                            <Text>Loading...</Text>
                                                        </Stack>
                                                    )}
                                                </Stack>
                                            </Stack>
                                        </Box>
                                    </HStack>
                                </TabPanel>
                            </TabPanels>
                        </Tabs>
                    </Stack>
                </ModalBody>
            </ModalContent>
        </Modal>
    )
}

export default AiAnalysisModal
