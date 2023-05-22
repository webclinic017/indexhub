import React from "react";
import { Text, VStack } from "@chakra-ui/react";
import { Outlet } from "react-router-dom";

export default function Objectives() {
  return (
    <VStack>
      <Text fontSize="2xl" fontWeight="bold" width="100%" textAlign="left">
        Objectives
      </Text>
      <Outlet />
    </VStack>
  );
}
