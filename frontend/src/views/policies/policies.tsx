import React from "react";
import { Text, VStack } from "@chakra-ui/react";
import { Outlet } from "react-router-dom";

export default function Policies() {
  return (
    <VStack padding="10px">
      <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">
        Policies
      </Text>
      <Outlet />
    </VStack>
  );
}
