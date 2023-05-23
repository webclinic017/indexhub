import React, { useContext, useEffect, useState } from "react";
import { Box, Flex, Divider, VStack } from "@chakra-ui/react";
import useWebSocket from "react-use-websocket";
import ChatMessageView, { Action, ChatMessage } from "./messages";
import ChatFooter from "./footer";
import { TrendsContext } from "../trends_dashboard";
import { ProjectorData } from "../projector/projector";


interface CopilotResponse {
    chatResponse: ChatMessage;
    channel: number;
}

const ChatWindow = () => {
    const { sendMessage, lastMessage, readyState } = useWebSocket(
        `${process.env.REACT_APP__FASTAPI__WEBSOCKET_DOMAIN}/copilot/ws`, {
        shouldReconnect: (closeEvent) => true,
    });


    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputMessage, setInputMessage] = useState("");
    const { selectedPointIds, apiToken, projectorData } = useContext(TrendsContext);

    useEffect(() => {
        if (lastMessage?.data) {
            const data = JSON.parse(lastMessage?.data)
            if (Object.keys(data).includes("chat_response")) {
                const { chatResponse, channel } = data.chat_response as CopilotResponse;
                setMessages((old) => [...old, chatResponse]);
            }
        }
    }, [lastMessage])

    const handleSendMessage = (action: Action) => {
        if (!inputMessage.trim().length) {
            return;
        }
        // Depending on the action, we need to prepare the message differently.
        // For example, if the action is "describe", we need to include the selected entity ids.
        // If the action is "chat", we only need to include the input message.
        // We should sanitize the input message to prevent XSS attacks.
        const sanitizedInputMessage = inputMessage;
        let message: ChatMessage;
        switch (action) {
            case "describe":
                message = getDescribeRequest(sanitizedInputMessage, selectedPointIds, projectorData);
                break;
            default:
                message = getBasicChatRequest(sanitizedInputMessage);
                break;
        }
        const fullMessage = {
            message_history: messages,
            request: message,
        };
        console.log(`sending message: ${JSON.stringify(fullMessage)}`);
        sendMessage(JSON.stringify(fullMessage));
        setMessages((old) => [...old, message]);
        setInputMessage("");
    };
    return (
        <Flex id="trends-sidebar-chat-window" w="100%" h="100" justify="center" align="center" boxShadow="xs" margin="5px">
            <VStack>
                <ChatMessageView messages={messages} />
                <ChatFooter
                    inputMessage={inputMessage}
                    setInputMessage={setInputMessage}
                    handleSendMessage={handleSendMessage}
                />
            </VStack >
        </Flex >
    );
}

const getBasicChatRequest = (msg: string): ChatMessage => {
    const newMessage: ChatMessage = {
        role: "user",
        action: "chat",
        channel: 0,
        additional_type: null,
        props: null,
        content: msg,
    };
    return newMessage;
};



const getDescribeRequest = (
    msg: string,
    selectedPointIds: number[],
    projectorData: ProjectorData
): ChatMessage => {
    const entities = selectedPointIds.map((pointId) => projectorData.entityIds[pointId]);
    const newMessage: ChatMessage = {
        role: "user",
        action: "describe",
        channel: 0,
        additional_type: "trend",
        props: {
            ids: selectedPointIds,
            entities: entities,
        },
        content: msg,
    };
    return newMessage;
};

export default ChatWindow;