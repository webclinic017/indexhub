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
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { MultiValue, Select } from "chakra-react-select";
import React, { useState } from "react";

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

const PolicyConfigs = (props: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  policies_schema: Record<any, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  policy_configs: Record<string, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  submitPolicyConfigs: (policy_configs: Record<string, any>) => void;
  goToPrevStep: () => void;
}) => {
  const policy_configs = props.policy_configs;
  const schema_config_fields =
    props.policies_schema[props.policy_configs["policy_type"]]["fields"];

  const [description, setDescription] = useState<string>(
    props.policies_schema[policy_configs["policy_type"]]["objective"]
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const updateDescription = (internal_policy_configs: Record<string, any>) => {
    let internal_description: string =
      props.policies_schema[internal_policy_configs["policy_type"]][
      "objective"
      ];
    internal_description = internal_description
      .replace(
        "{direction}",
        internal_policy_configs["direction"]
          ? internal_policy_configs["direction"]
          : "{direction}"
      )
      .replace(
        "{target_col}",
        internal_policy_configs["target_col"]
          ? internal_policy_configs["target_col"].replaceAll("_", " ")
          : "{target_col}"
      )
      .replace(
        "{level_cols}",
        internal_policy_configs["level_cols"]?.length > 0
          ? internal_policy_configs["level_cols"].join(" and ")
          : "{level_cols}"
      )
      .replace(
        "{error_type}",
        internal_policy_configs["error_type"]?.length > 0
          ? internal_policy_configs["error_type"]
          : "{error_type}"
      )
    policy_configs["policy_description"] = internal_description;
    setDescription(internal_description);
  };

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
          <Grid templateColumns="auto auto" gap={6} maxH="20rem" overflowY="scroll">
            <FormControl isRequired>
              <FormLabel>Policy name</FormLabel>
              <Input
                onChange={(e) =>
                  (policy_configs["policy_name"] = e.currentTarget.value)
                }
                placeholder="Name for your new policy"
              />
            </FormControl>
            {Object.keys(schema_config_fields).map(
              (config_field: string, idx: number) => {
                let depends_on = "";
                const has_depends_on = Object.keys(
                  schema_config_fields[config_field]
                ).includes("depends_on");
                if (has_depends_on) {
                  depends_on = schema_config_fields[config_field]["depends_on"];
                }
                const is_multiple = schema_config_fields[config_field][
                  "multiple_choice"
                ]
                  ? true
                  : false;
                return (
                  <FormControl isRequired key={idx}>
                    <FormLabel>
                      {schema_config_fields[config_field]["title"]}
                    </FormLabel>
                    <Select
                      isMulti={is_multiple ? true : false}
                      onChange={(value) => {
                        policy_configs[config_field] = value
                          ? is_multiple
                            ? getValuesArray(value)
                            : value.value
                          : "";
                        updateDescription(policy_configs);
                      }}
                      useBasicStyles
                      options={
                        has_depends_on
                          ? getOptionsArray(
                            schema_config_fields[config_field]["values"][
                            policy_configs[depends_on]
                            ]
                          )
                          : getOptionsArray(
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
          onClick={() => props.submitPolicyConfigs(policy_configs)}
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

export default PolicyConfigs;
