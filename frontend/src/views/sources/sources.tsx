import React, { useEffect, useState} from "react";
import { Container, Text, VStack } from '@chakra-ui/react'
import { Outlet } from "react-router-dom";


export default function Sources() {
  return (
    <VStack padding="10px">
      <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">Sources</Text>
      <Outlet></Outlet>
    </VStack>
  )
}
