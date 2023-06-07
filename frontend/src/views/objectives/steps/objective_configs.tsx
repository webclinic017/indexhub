import {
  Box,
  Button,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  Grid,
  HStack,
  Input,
  Spinner,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { MultiValue, Select } from "chakra-react-select";
import React, { useEffect, useState } from "react";

const getOptionsArray = (options: string[]) => {
  const result_options: any[] = []; // eslint-disable-line @typescript-eslint/no-explicit-any
  options.forEach((option: string) => {
    result_options.push({
      label: option,
      value: option,
    });
  });
  return result_options;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const getValuesArray = (values: MultiValue<Record<any, string>>) => {
  const values_array: string[] = [];
  values.map((value) => {
    values_array.push(value.value);
  });
  return values_array;
};

const ObjectiveConfigs = (props: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  objectives_schema: Record<any, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  objective_configs: Record<string, any>;
  panel_source_data_fields: Record<string, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  submitObjectiveConfigs: (objective_configs: Record<string, any>) => void;
  goToPrevStep: () => void;
}) => {
  const objective_configs = props.objective_configs;
  const schema_config_fields =
    props.objectives_schema[props.objective_configs["objective_type"]]["fields"];

  const [description, setDescription] = useState<string>(
    props.objectives_schema[objective_configs["objective_type"]]["objective"]
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const updateDescription = (internal_objective_configs: Record<string, any>) => {
    let internal_description: string =
      props.objectives_schema[internal_objective_configs["objective_type"]][
      "objective"
      ];
    internal_description = internal_description
      .replace(
        "{direction}",
        internal_objective_configs["direction"]
          ? internal_objective_configs["direction"]
          : "{direction}"
      )
      .replace(
        "{target_col}",
        props.panel_source_data_fields["target_col"]
          ? props.panel_source_data_fields["target_col"].replaceAll("_", " ")
          : "{target_col}"
      )
      .replace(
        "{entity_cols}",
        props.panel_source_data_fields["entity_cols"]?.length > 0
          ? props.panel_source_data_fields["entity_cols"].join(" and ")
          : "{entity_cols}"
      )
      .replace(
        "{error_type}",
        internal_objective_configs["error_type"]?.length > 0
          ? internal_objective_configs["error_type"]
          : "{error_type}"
      )
    objective_configs["objective_description"] = internal_description;
    setDescription(internal_description);
  };

  useEffect(() => {
    if (props.panel_source_data_fields) {
      updateDescription(objective_configs)
    }
  }, [props.panel_source_data_fields])

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
        <VStack>
          <VStack pb="2rem">
            <Text>{description}</Text>
          </VStack>
          <Grid templateColumns="auto auto" gap={6}>
            <FormControl isRequired>
              <FormLabel>Objective name</FormLabel>
              <Input
                onChange={(e) =>
                  (objective_configs["objective_name"] = e.currentTarget.value)
                }
                placeholder="Name for your new objective"
              />
            </FormControl>
            {Object.keys(schema_config_fields).map(
              (config_field: string, idx: number) => {

                const is_multiple = schema_config_fields[config_field][
                  "is_multiple"
                ]
                  ? true
                  : false;

                const is_required = schema_config_fields[config_field][
                  "is_required"
                ]
                  ? true
                  : false;
                return (
                  <FormControl isRequired={is_required} key={idx}>
                    <FormLabel>
                      {schema_config_fields[config_field]["title"]}
                    </FormLabel>
                    <Select
                      isMulti={is_multiple ? true : false}
                      onChange={(value) => {
                        objective_configs[config_field] = value
                          ? is_multiple
                            ? getValuesArray(value)
                            : value.value
                          : "";
                        updateDescription(objective_configs);
                      }}
                      useBasicStyles
                      options={
                        getOptionsArray(
                          schema_config_fields[config_field]["values"]
                        )
                      }
                    />
                  </FormControl>
                );
              }
            )}
          </Grid>
        </VStack>
      </Stack>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          onClick={() => props.submitObjectiveConfigs(objective_configs)}
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

export default ObjectiveConfigs;
