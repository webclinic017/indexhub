import React, { useState } from "react";
import {
  Box,
  Button,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  Input,
  Stack,
} from "@chakra-ui/react";
import { Select } from "chakra-react-select";

const getOptions = (options: string[]) => {
  const result_options: any[] = [];
  options.forEach((option: string) => {
    result_options.push({
      label: option,
      value: option,
    });
  });
  return result_options;
};

const SourcePath = (props: {
  source_tag: string;
  conn_schema: Record<string, any>;
  goToPrevStep: () => void;
  submitSourcePath: (configs: Record<string, string>) => Promise<void>;
  isLoadingSourceColumns: boolean;
}) => {
  // const configs: Record<string, string> = {};
  const [configs, setConfigs] = useState<Record<string, string>>({});

  const schema_variables: Record<string, any> =
    props.conn_schema[props.source_tag]["conn_fields"];

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
        <FormControl isRequired>
          <FormLabel>Source name</FormLabel>
          <Input
            onChange={(e) => {
              configs["source_name"] = e.currentTarget.value;
              setConfigs(structuredClone(configs));
            }}
            placeholder="Name for your new source"
          />
        </FormControl>
        {Object.keys(schema_variables).map((variable: string, idx: number) => {
          const has_values = Object.keys(schema_variables[variable]).includes(
            "values"
          );
          return (
            <FormControl isRequired key={idx}>
              <FormLabel>{schema_variables[variable]["title"]}</FormLabel>
              {!has_values && (
                <Input
                  onChange={(e) => {
                    configs[variable] = e.currentTarget.value;
                    setConfigs(structuredClone(configs));
                  }}
                />
              )}
              {has_values && (
                <Select
                  onChange={(value) => {
                    configs[variable] = value ? value.value : "";
                    setConfigs(structuredClone(configs));
                  }}
                  useBasicStyles
                  options={getOptions(schema_variables[variable]["values"])}
                />
              )}
            </FormControl>
          );
        })}
      </Stack>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          onClick={() => props.submitSourcePath(configs)}
          colorScheme="facebook"
          ml="2rem"
          isLoading={props.isLoadingSourceColumns}
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

export default SourcePath;
