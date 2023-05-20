import React from "react";
import { VStack } from "@chakra-ui/react";
import { Outlet, useLocation } from "react-router-dom";

interface propState {
  new_report: boolean;
}

export default function Data() {
  const location = useLocation();
  let new_report_state = false;

  if (location.state) {
    const { new_report } = location.state as propState;
    new_report_state = new_report;
  }
  return (
    <VStack px="6">
      <Outlet context={{ new_report: new_report_state }}></Outlet>
    </VStack>
  );
}
