import React, { useEffect, useRef } from "react";
import { Flex, Text, VStack, ListItem, UnorderedList } from "@chakra-ui/react";
import { VegaChart } from "../trends/charts";
import { useChatContext } from "./chat_context";

export type Role = "user" | "assistant";
export type Action = "chat" | "load_context" | "loading_response" | "stream_chat";
export type AdditionalType = "chart" | "metric" | "trend";


export interface ChatMessage {
    role: Role;
    action: Action;
    additional_type: AdditionalType | null;
    channel: number | null;
    props: Record<string, any> | null;
    content: string;
}


const ChatMessageView = () => {
    const { messages } = useChatContext();

    const AlwaysScrollToBottom = () => {
        const elementRef = useRef<null | HTMLDivElement>(null);
        useEffect(() => {
            if (elementRef.current) {
                elementRef.current.scrollIntoView();
            }
        })
        return <div ref={elementRef} />;
    };

    return (
        <Flex id="trends-sidebar-chat-messages" h="100%" w="100%" overflowY="scroll" flexDirection="column">
            <UnorderedList>
                {messages.map((msg, index) =>
                    <ListItem key={index} margin={"10px"} listStyleType='none'>
                        <Flex key={index} w="100%" justify={msg.role === "user" ? "flex-end" : "flex-start"}>
                            <ChatItem msg={msg} />
                        </Flex>
                    </ListItem>
                )}
            </UnorderedList>
            <AlwaysScrollToBottom />
        </Flex >
    )

};


const ChatItem = (props: { msg: ChatMessage }) => {
    const { msg } = props;
    switch (msg.action) {
        case "stream_chat":
            return <StreamChatRepsonse msg={msg} />
        case "load_context":
            return <LoadContextResponse msg={msg} />
        case "loading_response":
            return <LoadingResponse msg={msg} />
        default:
            return <ChatResponse msg={msg} />
    }
}

const ChatResponse = (props: { msg: ChatMessage }) => {
    const { msg } = props;
    return (
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
    )
}

const StreamChatRepsonse = (props: { msg: ChatMessage }) => {
    const { msg } = props;
    return (
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
    )
}

const LoadContextResponse = (props: { msg: ChatMessage }) => {
    const { msg } = props;
    return (
        <VStack
            bg={msg.role === "user" ? "black" : "gray.100"}
            color={msg.role === "user" ? "white" : "black"}
            minW="100px"
            maxW="90%"
            my="1"
            p="3"
            borderRadius={8}
        >,
            {msg.props === null ? <></> : <VegaChart entityId={msg.props?.entity_id} spec={msg.props?.chart as string} />}
            <Text mt="unset !important">{msg.content}</Text>
        </VStack>
    );
};

const LoadingResponse = (props: { msg: ChatMessage }) => {
    const { msg } = props;
    return (
        <VStack
            bg={msg.role === "user" ? "black" : "gray.100"}
            color={msg.role === "user" ? "white" : "black"}
            minW="100px"
            maxW="90%"
            my="1"
            p="3"
            borderRadius={8}
        >,
            <div className="spinner">
                <div className="bounce1"></div>
                <div className="bounce2"></div>
                <div className="bounce3"></div>
            </div>
        </VStack>
    );
};

export default ChatMessageView;