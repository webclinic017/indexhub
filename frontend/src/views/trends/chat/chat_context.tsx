import React, { createContext, useContext, useEffect, useState } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { Action, ChatMessage } from "./messages";

export const useChatContext = () => useContext(ChatContext);

export const ChatContext = createContext({
    messages: [] as ChatMessage[],
    inputMessage: "",
    setInputMessage: (_inputMessage: string) => { /* do nothing */ },
    handleSendMessage: (_action: Action, _props?: Record<string, any>) => { /* do nothing */ },
});

interface ChatResponse {
    response: ChatMessage;
    channel: number;
}

const ChatContextProvider = (props: { children: React.ReactNode }) => {
    const { sendMessage, readyState, sendJsonMessage, lastJsonMessage } = useWebSocket(
        `${process.env.REACT_APP__FASTAPI__WEBSOCKET_DOMAIN}/trends/copilot/ws`, {
        shouldReconnect: (_closeEvent) => true,
    });
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputMessage, setInputMessage] = useState("");

    // Websocket lifecycle
    useEffect(() => {
        if (readyState === ReadyState.OPEN) {
            console.log("Chat window websocket open");
            const config = { user_id: "TEST_USER" };
            sendJsonMessage(config);
        } else if (readyState === ReadyState.CLOSED) {
            console.log("Chat window websocket closed");
        } else if (readyState === ReadyState.CONNECTING) {
            console.log("Chat window websocket connecting");
        } else if (readyState === ReadyState.CLOSING) {
            console.log("Chat window websocket closing");
        }
    }, [readyState])

    useEffect(() => {
        if (lastJsonMessage !== null) {
            console.log(`received message: ${JSON.stringify(lastJsonMessage)}:${typeof lastJsonMessage}`);
            const data = lastJsonMessage as Record<string, any>;
            if (Object.keys(data).includes("response")) {
                const response = data["response"];
                console.log(`received response: ${response}:${typeof response}`);
                setMessages((old) => [...old, response]);
            }
        }
    }, [lastJsonMessage])

    const handleSendMessage = (action: Action, props?: Record<string, any>) => {
        console.log(`handleSendMessage: ${action}`);

        // Depending on the action, we need to prepare the message differently.
        // For example, if the action is "describe", we need to include the selected entity ids.
        // If the action is "chat", we only need to include the input message.
        // We should sanitize the input message to prevent XSS attacks.
        const sanitizedInputMessage = inputMessage;
        let request: ChatMessage;
        switch (action) {
            case "load_context":
                console.log(`loadContextRequest: ${JSON.stringify(props)}`);
                if (props === undefined) {
                    throw new Error("props must be defined for load_context action");
                }
                request = getLoadContextRequest(sanitizedInputMessage, props);
                break;
            default:
                console.log("getBasicChatRequest");
                request = getBasicChatRequest(sanitizedInputMessage);
                break;
        }
        const fullMessage = {
            message_history: messages.map((msg) => ({ "role": msg.role, "content": msg.content })),
            request: request,
        };
        console.log(`sending message: ${JSON.stringify(fullMessage)}`);
        // Using sendMessage instead of sendJsonMessage because there is some type error
        sendMessage(JSON.stringify(fullMessage));
        setMessages((old) => [...old, request]);
        setInputMessage("");
    };


    useEffect(() => {
        console.log(`messages: ${JSON.stringify(messages)}`);
    }, [messages]);
    return (
        <ChatContext.Provider value={{
            messages,
            handleSendMessage,
            inputMessage,
            setInputMessage
        }}>
            {props.children}
        </ChatContext.Provider>
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

const getLoadContextRequest = (
    msg: string,
    props: Record<string, any>
): ChatMessage => {
    const newMessage: ChatMessage = {
        role: "user",
        action: "load_context",
        channel: 0,
        additional_type: "trend",
        props: {
            dataset_id: props["dataset_id"],
            entity_id: props["entity_id"],
        },
        content: msg,
    };
    return newMessage;
};

export default ChatContextProvider;