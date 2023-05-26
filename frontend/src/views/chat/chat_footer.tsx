import React, { useState } from "react";
import { Flex, Input, Button, VStack, UnorderedList, Text } from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPaperPlane } from "@fortawesome/pro-light-svg-icons";
import { Action } from "./chat_body";
import { useChatContext } from "./chat_context";


const ChatFooter = () => {
    const { inputMessage, setInputMessage, handleSendMessage } = useChatContext();
    const [actions, setActions] = useState<Action[]>([]);

    return (
        <VStack id="trends-sidebar-chat-footer" w="100%">
            {/* <SuggestedInputs inputMessage={inputMessage} handleSendMessage={handleSendMessage} actions={actions} /> */}
            <ChatInput inputMessage={inputMessage} setInputMessage={setInputMessage} handleSendMessage={handleSendMessage} />
        </VStack>
    );
};

interface SuggestedActionsProps {
    inputMessage: string;
    handleSendMessage: (action: Action) => void;
    actions?: Action[];
}
const SuggestedInputs = (props: SuggestedActionsProps) => {
    const { inputMessage, handleSendMessage, actions } = props;

    return (
        <Flex width="100%" justify="center" align="center">
            {actions !== undefined ? (
                <UnorderedList display="flex" listStyleType="none" pl={0}>
                    {actions.map((action, index) => {
                        return (
                            <Button
                                key={index}
                                bg="black"
                                color="white"
                                borderRadius={8}
                                _hover={{
                                    bg: "white",
                                    color: "black",
                                    border: "1px solid black",
                                }}
                                ml="5px"
                                disabled={inputMessage.trim().length <= 0}
                                onClick={() => handleSendMessage(action)}
                            >
                                AI {action}
                            </Button>);
                    })
                    }
                </UnorderedList>) : <Text width={"100%"}>No actions available</Text>}
        </Flex>
    );
};

interface ChatInputProps {
    inputMessage: string;
    setInputMessage: (inputMessage: string) => void;
    handleSendMessage: (action: Action) => void;
}

const ChatInput = (props: ChatInputProps) => {
    const { inputMessage, setInputMessage, handleSendMessage } = props;
    return (
        <Flex w="100%" mt="5">
            <Input
                placeholder="Type Something..."
                border={"1px solid grey"}
                borderRadius={8}
                w={"100%"}
                _focus={{
                    border: "1px solid black",
                }}
                onKeyPress={(e) => {
                    if (e.key === "Enter") {
                        handleSendMessage("stream_chat");
                    }
                }}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
            />
            <Button
                bg="black"
                color="white"
                borderRadius={8}
                border="1px solid black"
                _hover={{
                    bg: "white",
                    color: "black",
                }}
                ml="5px"
                disabled={inputMessage.trim().length <= 0}
                onClick={() => handleSendMessage("stream_chat")}
            >
                <FontAwesomeIcon icon={faPaperPlane as any} />
            </Button>
        </Flex>
    );
};


export default ChatFooter;