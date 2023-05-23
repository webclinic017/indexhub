import React from "react";
import { Text, VStack } from "@chakra-ui/react";
import { Outlet } from "react-router-dom";

export default function Trends() {
    return (
        <VStack>
            <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">
                Trends
            </Text>
            <Outlet />
        </VStack>
    );
}
