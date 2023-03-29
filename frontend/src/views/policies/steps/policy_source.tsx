import {
  Box,
  Button,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  Stack,
} from "@chakra-ui/react";
import { Select } from "chakra-react-select";
import React from "react";

const getOptionsSource = (sources: Record<string, string>) => {
  const result: Record<string, string>[] = []; // eslint-disable-line @typescript-eslint/no-explicit-any
  Object.keys(sources).forEach((source_name) => {
    result.push({
      value: sources[source_name],
      label: source_name,
    });
  });
  return result;
};

const PolicySource = (props: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  policies_schema: Record<any, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  policy_configs: Record<string, any>;
  submitPolicySources: (policy_sources: Record<string, string>) => void;
  goToPrevStep: () => void;
}) => {
  const schema_dataset_fields =
    props.policies_schema[props.policy_configs["policy_type"]]["datasets"];
  const policy_sources: Record<string, string> = {};

  return (
    <Box
      as="form"
      borderColor="forms.border"
      borderWidth="1px"
      borderStyle="solid"
      borderRadius="lg"
    >
      <Stack
        spacing="5"
        px={{ base: "4", md: "6" }}
        py={{ base: "5", md: "6" }}
      >
        {Object.keys(schema_dataset_fields).map(
          (dataset_field: string, idx: number) => {
            return (
              <FormControl isRequired key={idx}>
                <FormLabel>
                  {schema_dataset_fields[dataset_field]["title"]}
                </FormLabel>
                <Select
                  onChange={(value) => {
                    policy_sources[dataset_field] = value ? value.value : "";
                    policy_sources[`${dataset_field}_name`] = value
                      ? value.label
                      : "";
                  }}
                  useBasicStyles
                  options={getOptionsSource(
                    schema_dataset_fields[dataset_field]["values"]
                  )}
                />
              </FormControl>
            );
          }
        )}
      </Stack>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          onClick={() => props.submitPolicySources(policy_sources)}
          colorScheme="facebook"
          ml="2rem"
        >
          Next
        </Button>
        <Button onClick={() => props.goToPrevStep()} colorScheme="facebook">
          Prev
        </Button>
      </Flex>
    </Box>
  );
};

export default PolicySource;
