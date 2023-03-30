import {
  Box,
  Button,
  Divider,
  Flex,
  Stack,
  Text,
  StackDivider,
  Container,
} from "@chakra-ui/react";

import React from "react";

const ConfirmCreatePolicy = (props: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  policy_configs: Record<string, any>;
  createPolicy: () => Promise<void>;
  goToPrevStep: () => void;
}) => {
  return (
    <Box
      as="form"
      borderColor="forms.border"
      borderWidth="1px"
      borderStyle="solid"
      borderRadius="lg"
    >
      <Box bgColor={"forms.bg_grey"} borderTopRadius="lg">
        <Text py="1rem" pl="1rem" color="muted" fontSize="sm">
          An overview of your new policy setup
        </Text>
      </Box>
      <Divider />
      <Container maxWidth="unset" py="1rem">
        <Stack spacing="5">
          <Stack spacing="5" divider={<StackDivider />}>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Policy name:
              </Text>
              <Text width="70%">{props.policy_configs["policy_name"]}</Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Policy type:
              </Text>
              <Text width="70%">{props.policy_configs["policy_type"]}</Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Panel source:
              </Text>
              <Text width="70%">{props.policy_configs["panel_name"]}</Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Baseline source:
              </Text>
              <Text width="70%">{props.policy_configs["baseline_name"]}</Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Policy description:
              </Text>
              <Text width="70%">
                {props.policy_configs["policy_description"]}
              </Text>
            </Stack>
          </Stack>
        </Stack>
      </Container>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          ml="2rem"
          onClick={() => props.createPolicy()}
          colorScheme="facebook"
        >
          Create policy
        </Button>
        <Button onClick={() => props.goToPrevStep()} colorScheme="facebook">
          Prev
        </Button>
      </Flex>
    </Box>
  );
};

export default ConfirmCreatePolicy;
