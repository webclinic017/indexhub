import React from "react";
import { Drawer, DrawerBody, DrawerCloseButton, DrawerContent, DrawerFooter, DrawerHeader, DrawerOverlay, Flex } from "@chakra-ui/react"
import ChatMessageView from "../chat/chat_body";
import ChatFooter from "../chat/chat_footer";

const ChatBot = (props: {
    isOpen: boolean,
    onOpen: () => void,
    onClose: () => void
}) => {
    return (
        <>
            <Drawer
                isOpen={props.isOpen}
                placement='right'
                onClose={props.onClose}
                size="md"
            >
                <DrawerOverlay />
                <DrawerContent>
                    <DrawerCloseButton />
                    <DrawerHeader>IndexBot</DrawerHeader>
                    <DrawerBody>
                        <Flex w="100%" overflowY="scroll" flexDirection="column">
                            <ChatMessageView />
                        </Flex>
                    </DrawerBody>
                    <DrawerFooter>
                        <ChatFooter />
                    </DrawerFooter>
                </DrawerContent>
            </Drawer>
        </>
    )
}

export default ChatBot