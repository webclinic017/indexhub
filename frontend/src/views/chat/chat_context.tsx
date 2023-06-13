import React, { createContext, useContext, useEffect, useState } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { Action, ChatMessage } from "./chat_body";
import { useDisclosure } from "@chakra-ui/react";

export const useChatContext = () => useContext(ChatContext);

export const ChatContext = createContext({
  messages: [] as ChatMessage[],
  inputMessage: "",
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setInputMessage: (_inputMessage: string) => {
    /* do nothing */
  },
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  handleSendMessage: (_action: Action, _props?: Record<string, any>) => {
    /* do nothing */
  },
  isOpenChatBot: false,
  onOpenChatBot: () => {
    /* do nothing */
  },
  onCloseChatBot: () => {
    /* do nothing */
  },
});

const ChatContextProvider = (props: { children: React.ReactNode }) => {
  const { sendMessage, readyState, sendJsonMessage, lastJsonMessage } =
    useWebSocket(
      `${process.env.REACT_APP__FASTAPI__WEBSOCKET_DOMAIN}/trends/copilot/ws`,
      {
        shouldReconnect: (_closeEvent) => false, // eslint-disable-line @typescript-eslint/no-unused-vars
      }
    );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const {
    isOpen: isOpenChatBot,
    onOpen: onOpenChatBot,
    onClose: onCloseChatBot,
  } = useDisclosure();

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
  }, [readyState]);

  useEffect(() => {
    if (lastJsonMessage !== null) {
      // console.log(`received message: ${JSON.stringify(lastJsonMessage)}:${typeof lastJsonMessage}`);
      const data = lastJsonMessage as Record<string, any>;
      if (Object.keys(data).includes("response")) {
        const response = data["response"];
        // console.log(`received response: ${response}:${typeof response}`);
        setMessages((old) => {
          // First check what the last message was.
          // Case 0: No messages -> add the response
          if (old.length === 0) {
            return [response];
          }
          // Case 1: Last message is a stream -> modify the last response
          const lastMessage = old[old.length - 1];
          if (
            lastMessage.action === "stream_chat" &&
            lastMessage.role === "assistant"
          ) {
            // TODO: Fix edge case: Strict mode rendering twice
            // Solution: Check if the last message has already been updated
            console.log(
              `parts: ${lastMessage.props?.part}:${response.props?.part}`
            );
            const lastPart = lastMessage.props?.part;
            const newPart = response.props?.part;
            if (lastPart === newPart) {
              return old;
            }
            const updatedList = [...old]; // Create a copy of the original list
            const newLastMsg = updatedList[updatedList.length - 1];
            newLastMsg.content += response.content; // Update the content
            newLastMsg.props = { ...response.props }; // Update the props

            return updatedList; // Return the updated list
          }

          // Default case: remove loading and add the response
          old = old.filter((msg) => msg.action !== "loading_response");
          return [...old, response];
        });
      }
    }
  }, [lastJsonMessage]);

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
        console.log("loadContextRequest");
        if (props === undefined) {
          throw new Error("props must be defined for load_context action");
        }
        request = getLoadContextRequest(props);
        break;
      case "stream_chat":
        console.log("getBasicChatRequest");
        request = getStreamChatRequest(sanitizedInputMessage);
        break;
      default:
        console.log("getBasicChatRequest");
        request = getBasicChatRequest(sanitizedInputMessage);
        break;
    }
    const fullMessage = {
      message_history: messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
      request: request,
    };
    const loadingResponse: ChatMessage = {
      role: "assistant",
      action: "loading_response",
      channel: 0,
      additional_type: null,
      props: null,
      content: "Loading",
    };
    // console.log(`sending message: ${JSON.stringify(fullMessage)}`);
    // Using sendMessage instead of sendJsonMessage because there is some type error
    sendMessage(JSON.stringify(fullMessage));
    setMessages((old) => [...old, request, loadingResponse]);
    setInputMessage("");
  };

  // useEffect(() => {
  //     console.log(`messages: ${JSON.stringify(messages)}`);
  // }, [messages]);
  return (
    <ChatContext.Provider
      value={{
        messages,
        handleSendMessage,
        inputMessage,
        setInputMessage,
        isOpenChatBot,
        onOpenChatBot,
        onCloseChatBot,
      }}
    >
      {props.children}
    </ChatContext.Provider>
  );
};
const getStreamChatRequest = (msg: string): ChatMessage => {
  const newMessage: ChatMessage = {
    role: "user",
    action: "stream_chat",
    channel: 0,
    additional_type: null,
    props: null,
    content: msg,
  };
  return newMessage;
};

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

const getLoadContextRequest = (props: Record<string, any>): ChatMessage => {
  const newMessage: ChatMessage = {
    role: "user",
    action: "load_context",
    channel: 0,
    additional_type: "trend",
    props: {
      dataset_id: props["dataset_id"],
      entity_id: props["entity_id"],
    },
    content: `Let's look at ${props["entity_id"]}.`,
  };
  return newMessage;
};

export default ChatContextProvider;
