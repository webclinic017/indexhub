import React, { useContext, useEffect, useState } from "react";
import { Flex, Input, Button, VStack, UnorderedList, Text } from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPaperPlane } from "@fortawesome/pro-light-svg-icons";
import { Action } from "./messages";
import { TrendsContext } from "../trends_dashboard";

interface ChatFooterProps {
    inputMessage: string;
    setInputMessage: (inputMessage: string) => void;
    handleSendMessage: (action: Action) => void;
}
const ChatFooter = (props: ChatFooterProps) => {
    const { inputMessage, setInputMessage, handleSendMessage } = props;
    const [actions, setActions] = useState<Action[]>([]);
    const { selectedPointIds } = useContext(TrendsContext);

    useEffect(() => {
        if (selectedPointIds.length === 0) {
            setActions([]);
        } else {
            setActions(["describe"]);
        }
    }, [selectedPointIds]);
    return (
        <VStack id="trends-sidebar-chat-footer" w="100%">
            <SuggestedActions inputMessage={inputMessage} handleSendMessage={handleSendMessage} actions={actions} />
            <ChatInput inputMessage={inputMessage} setInputMessage={setInputMessage} handleSendMessage={handleSendMessage} />
        </VStack>
    );
};
interface SuggestedActionsProps {
    inputMessage: string;
    handleSendMessage: (action: Action) => void;
    actions?: Action[];
}
const SuggestedActions = (props: SuggestedActionsProps) => {
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
                border="none"
                borderRadius="none"
                w={"100%"}
                _focus={{
                    border: "1px solid black",
                }}
                onKeyPress={(e) => {
                    if (e.key === "Enter") {
                        handleSendMessage("chat");
                    }
                }}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
            />
            <Button
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
                onClick={() => handleSendMessage("chat")}
            >
                <FontAwesomeIcon icon={faPaperPlane as any} />
            </Button>
        </Flex>
    );
};


export default ChatFooter;