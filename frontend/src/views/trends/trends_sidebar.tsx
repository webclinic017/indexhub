import React from "react";
import { Box, VStack } from '@chakra-ui/react';
import ChatWindow from "./chat/window";
import TrendsSidebarCharts from "./trends_sidebar_charts";

const TrendsSidebar = () => {
    return (
        <Box id="trends-sidebar" height="full" maxH='100%' maxW={'md'} boxShadow="xs" margin="5px" overflowY={"scroll"}>
            <VStack height="full" w='full' maxW={'md'}>
                <TrendsSidebarCharts />
                <ChatWindow /> 
            </VStack>
        </Box>
    )
}

export default TrendsSidebar;