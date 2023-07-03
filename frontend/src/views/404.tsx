import { Box, Button, Stack, Text, VStack } from "@chakra-ui/react";
import { faSpiderBlackWidow } from "@fortawesome/pro-light-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React from "react";
import { useNavigate } from "react-router-dom";

const NotFound404 = () => {
  const navigate = useNavigate();
  return (
    <Stack
      alignItems="center"
      justifyContent="center"
      height="100%"
      overflow="hidden"
    >
      <VStack height="50%" justify="flex-end">
        <Text fontSize="9xl" fontWeight="bold">
          404
        </Text>
        <Text>
          We can&apos;t seem to find the page you&apos;re looking for.
        </Text>
        <Button onClick={() => navigate("/")}>Back to Objectives</Button>
      </VStack>
      <VStack height="50%" justify="flex-end">
        <Box>
          <FontAwesomeIcon shake size="10x" icon={faSpiderBlackWidow} />
        </Box>
      </VStack>
    </Stack>
  );
};

export default NotFound404;
