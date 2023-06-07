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
  const result: Record<string, string>[] = [];
  Object.keys(sources).forEach((source_name) => {
    result.push({
      value: sources[source_name],
      label: source_name,
    });
  });
  return result;
};

const ObjectiveSource = (props: {
  objectives_schema: Record<any, any>;

  objective_configs: Record<string, any>;
  submitObjectiveSources: (objective_sources: Record<string, string>) => void;
  goToPrevStep: () => void;
}) => {
  const schema_dataset_fields =
    props.objectives_schema[props.objective_configs["objective_type"]][
      "sources"
    ];
  const objective_sources: Record<string, string> = {};

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
            const is_required = schema_dataset_fields[dataset_field][
              "is_required"
            ]
              ? true
              : false;
            return (
              <FormControl isRequired={is_required} key={idx}>
                <FormLabel>
                  {schema_dataset_fields[dataset_field]["title"]}
                </FormLabel>
                <Select
                  onChange={(value) => {
                    objective_sources[dataset_field] = value ? value.value : "";
                    objective_sources[`${dataset_field}_name`] = value
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
          onClick={() => props.submitObjectiveSources(objective_sources)}
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

export default ObjectiveSource;
