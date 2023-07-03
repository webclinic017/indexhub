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

const ConfirmCreateObjective = (props: {
  objective_configs: Record<string, any>;
  createObjective: () => void;
  goToPrevStep: () => void;
  isCreatingObjective: boolean;
}) => {
  return (
    <Box
      as="form"
      borderColor="forms.border"
      borderWidth="1px"
      borderStyle="solid"
      borderRadius="lg"
    >
      <Box bgColor={"forms.bg_gray"} borderTopRadius="lg">
        <Text py="1rem" pl="1rem" color="muted" fontSize="sm">
          An overview of your new objective setup
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
                Objective name:
              </Text>
              <Text width="70%">
                {props.objective_configs["objective_name"]}
              </Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Objective type:
              </Text>
              <Text width="70%">
                {props.objective_configs["objective_type"]}
              </Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Panel source:
              </Text>
              <Text width="70%">{props.objective_configs["panel_name"]}</Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Baseline source:
              </Text>
              <Text width="70%">
                {props.objective_configs["baseline_name"]}
              </Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Objective description:
              </Text>
              <Text width="70%">
                {props.objective_configs["objective_description"]}
              </Text>
            </Stack>
          </Stack>
        </Stack>
      </Container>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          ml="2rem"
          onClick={() => props.createObjective()}
          colorScheme="facebook"
          isLoading={props.isCreatingObjective}
        >
          Create objective
        </Button>
        <Button onClick={() => props.goToPrevStep()} colorScheme="facebook">
          Prev
        </Button>
      </Flex>
    </Box>
  );
};

export default ConfirmCreateObjective;
