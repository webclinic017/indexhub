import React from "react";
import { Text, VStack } from "@chakra-ui/react";
import { Outlet } from "react-router-dom";

export default function Objectives() {
  return (
    <VStack>
      <Outlet />
    </VStack>
  );
}
