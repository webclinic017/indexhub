import React from "react";
import { Flex, VStack } from '@chakra-ui/react';
import ChatMessageView from "./chat/messages";
import ChatFooter from "./chat/footer";

const TrendsSidebar = () => {
    return (
        <Flex width="100%" maxW={"md"} height="100%" justify="center" align="start">
            <VStack id="trends-sidebar-chat-window" w="100%" h="100%" justify="center" align="center" boxShadow="xs" margin="5px">
                <ChatMessageView />
                <ChatFooter />
            </VStack >
        </Flex>
    )
}

export default TrendsSidebar;