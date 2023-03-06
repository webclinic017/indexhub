import React from "react";
import { Text, VStack } from "@chakra-ui/react";
import { Outlet, useLocation } from "react-router-dom";

interface propState {
  new_report: boolean;
}

export default function Sources() {
  const location = useLocation();
  let new_report_state = false;

  if (location.state) {
    const { new_report } = location.state as propState;
    new_report_state = new_report;
  }
  return (
    <VStack padding="10px">
      <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">
        Sources
      </Text>
      <Outlet context={{ new_report: new_report_state }}></Outlet>
    </VStack>
  );
}
