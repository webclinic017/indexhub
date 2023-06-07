import React from "react";
import { VStack } from "@chakra-ui/react";
import { Outlet } from "react-router-dom";

export default function Objectives() {
  return (
    <VStack>
      <Outlet />
    </VStack>
  );
}
