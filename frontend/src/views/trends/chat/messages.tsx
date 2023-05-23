import React from "react";
import { Box, Flex, Text, VStack, ListItem, UnorderedList } from "@chakra-ui/react";


export type Role = "user" | "assistant";
export type Action = "chat" | "describe";
export type AdditionalType = "chart" | "metric" | "trend";


export interface ChatMessage {
    role: Role;
    action: Action;
    additional_type: AdditionalType | null;
    channel: number | null;
    props: Record<string, any> | null;
    content: string;
}
export interface ChatMessageViewProps {
    messages: ChatMessage[];
}

const ChatMessageView = (props: ChatMessageViewProps) => {
    const { messages } = props;
    return <Flex id="trends-sidebar-chat-messages" w="100%" overflowY="scroll" flexDirection="column">
        <UnorderedList>
            {messages.map((msg, index) =>
                <ListItem key={index}>
                    <ChatItem msg={msg} index={index} />
                </ListItem>
            )}
        </UnorderedList>
    </Flex>;
};


const ChatItem = (props: { msg: ChatMessage, index: number }) => {
    const { msg, index } = props;
    switch (msg.action) {
        case "describe":
            return <DescribeResponse msg={msg} index={index} />
        default:
            return <ChatResponse msg={msg} index={index} />
    }
}

const ChatResponse = (props: { msg: ChatMessage; index: number }) => {
    const { msg, index } = props;
    return (
        <Flex key={index} w="100%" justify={msg.role === "user" ? "flex-end" : "flex-start"}>
            <Flex
                bg={msg.role === "user" ? "black" : "gray.100"}
                color={msg.role === "user" ? "white" : "black"}
                minW="100px"
                maxW="90%"
                my="1"
                p="3"
                borderRadius={8}
            >
                <Text>{msg.content}</Text>
            </Flex>
        </Flex>
    )
}

const DescribeResponse = (props: { msg: ChatMessage; index: number }) => {
    const { msg, index } = props;
    return (
        <Flex key={index} w="100%" justify={msg.role === "user" ? "flex-end" : "flex-start"}>
            <VStack
                bg={msg.role === "user" ? "black" : "gray.100"}
                color={msg.role === "user" ? "white" : "black"}
                minW="100px"
                maxW="90%"
                my="1"
                p="3"
                borderRadius={8}
            >
                <Text>{msg.content}</Text>
            </VStack>
        </Flex>
    );
};


export default ChatMessageView;