import React from "react";
import { ErrorBoundary } from "react-error-boundary";
import { Box, Button, Stack, Text, VStack } from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSpiderBlackWidow } from "@fortawesome/pro-light-svg-icons";
import { useLocation } from "react-router-dom";

function ErrorPage({ resetErrorBoundary }: any) {
  return (
    <Stack
      alignItems="center"
      justifyContent="center"
      height="full"
      overflow="hidden"
    >
      <VStack height="50%" justify="flex-end">
        <Text fontSize="9xl" fontWeight="bold">
          500
        </Text>
        <Text>
          Look&apos;s like something went wrong on our side. Please try again
          later or contact our support if this issue persists.
        </Text>
        <Button onClick={resetErrorBoundary}>Back to Objectives</Button>
      </VStack>
      <VStack height="50%" justify="flex-end">
        <Box>
          <FontAwesomeIcon shake size="10x" icon={faSpiderBlackWidow} />
        </Box>
      </VStack>
    </Stack>
  );
}

export default function ReactErrorBoundary(props: any) {
  const location = useLocation();
  return (
    <ErrorBoundary
      FallbackComponent={ErrorPage}
      onReset={() => {
        window.location.pathname = "/";
      }}
      key={location.pathname}
    >
      {props.children}
    </ErrorBoundary>
  );
}
